(function () {
    var panelKeyword = document.getElementById("panel-keyword");
    var panelUrl = document.getElementById("panel-url");
    var modeButtons = document.querySelectorAll(".modes button");
    var formKeyword = document.getElementById("form-keyword");
    var formUrl = document.getElementById("form-url");
    var output = document.getElementById("output");
    var errorEl = document.getElementById("error");
    var btnKeyword = document.getElementById("btn-keyword");
    var btnUrl = document.getElementById("btn-url");

    function setMode(mode) {
        var isKeyword = mode === "keyword";
        panelKeyword.classList.toggle("visible", isKeyword);
        panelUrl.classList.toggle("visible", !isKeyword);
        modeButtons.forEach(function (b) {
            var active = b.getAttribute("data-mode") === mode;
            b.classList.toggle("active", active);
            b.setAttribute("aria-selected", active ? "true" : "false");
        });
        errorEl.textContent = "";
    }

    modeButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            setMode(btn.getAttribute("data-mode"));
        });
    });

    function showError(msg) {
        errorEl.textContent = msg || "";
    }

    function showOutput(data, status) {
        output.textContent = JSON.stringify({ status: status, body: data }, null, 2);
    }

    async function postJson(path, body, submitBtn) {
        var res = await fetch(path, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify(body),
        });
        var text = await res.text();
        var data;
        try {
            data = text ? JSON.parse(text) : null;
        } catch (e) {
            data = text;
        }
        return {res: res, data: data};
    }


    function sleep(ms) {
        return new Promise(function (resolve) {
            setTimeout(resolve, ms);
        });
    }

    async function pollJobUntilDone(job_id) {
        var interval_ms = 1000;
        var max_attempts = 100;

        for (var i = 0; i < max_attempts; i++) {
            var res = await fetch(
                "/api/v1/jobs/" + job_id,
                {headers: {Accept: "application/json"}},
            );
            var text = await res.text();
            var data;
            try {
                data = text ? JSON.parse(text) : null;
            } catch (e) {
                data = {status: "error", raw: text};
            }

            if (!res.ok) {
                var pollExtra =
                    typeof data === "object" && data && data.detail
                        ? ": " + JSON.stringify(data.detail)
                        : "";
                showError(res.status + " " + res.statusText + pollExtra);
                showOutput(data, res.status);
                return data;
            }

            if (data && data.status === "complete") {
                showOutput(data, res.status);
                return data;
            }
            if (data && (data.status === "failed" || data.status === "not_found")) {
                showError(data.error || data.status);
                showOutput(data, res.status);
                return data;
            }

            output.textContent =
                "Job " +
                job_id +
                "… status: " +
                (data && data.status ? data.status : "?") +
                " (" +
                (i + 1) +
                "/" +
                max_attempts +
                ")";
            
            await sleep(interval_ms);
        }
        showError("Timeout waiting for job");
        showOutput({ status: "timeout", job_id: job_id }, 0);
    }

    formKeyword.addEventListener("submit", function (e) {
        e.preventDefault();
        var keyword = document.getElementById("keyword").value.trim();
        var start_date = document.getElementById("start_date").value;
        var end_date = document.getElementById("end_date").value;
        if (!keyword || !start_date || !end_date) return;
        postJson(
            "/api/v1/search-and-summarize",
            {
                keyword: keyword,
                start_date: start_date,
                end_date: end_date,
            },
            btnKeyword,
        );
    });

    formUrl.addEventListener("submit", async function (e) {
        e.preventDefault();
        var url = document.getElementById("article_url").value.trim();
        if (!url) return;

        showError("");
        btnUrl.disabled = true;
        output.textContent = "Submitting…";

        try {
            var out = await postJson("/api/v1/summarize-url", { url: url });
            var res = out.res;
            var data = out.data;

            if (!res.ok) {
                var extra =
                    typeof data === "object" && data && data.detail
                        ? ": " + JSON.stringify(data.detail)
                        : "";
                showError(res.status + " " + res.statusText + extra);
                showOutput(data, res.status);
                return;
            }

            if (data && data.job_id) {
                await pollJobUntilDone(data.job_id);
            } else {
                showOutput(data, res.status);
            }
        } catch (err) {
            showError(err.message || String(err));
            showOutput(null, 0);
        } finally {
            btnUrl.disabled = false;
        }
    });

    (function defaults() {
        var end = new Date();
        var start = new Date(end);
        start.setDate(start.getDate() - 7);
        document.getElementById("end_date").valueAsDate = end;
        document.getElementById("start_date").valueAsDate = start;
    })();
})();
