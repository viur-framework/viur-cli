// Strip auto-generated `--help`-only Options blocks from mkdocs-click output.
//
// Click's --help is added to every command, so mkdocs-click renders an
// "Options:" section for every Click command/group even when there is
// nothing else to show. We hide those purely-noisy sections at view time.
document.addEventListener("DOMContentLoaded", () => {
    const isHelpOnly = (pre) => {
        const lines = pre.textContent
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l);
        return (
            lines.length > 0 &&
            lines.every((l) => /^-h,?\s*--help/.test(l))
        );
    };

    document.querySelectorAll("div.highlight").forEach((wrap) => {
        const pre = wrap.querySelector("pre");
        if (!pre || !isHelpOnly(pre)) return;

        const prev = wrap.previousElementSibling;
        if (
            prev &&
            prev.tagName === "P" &&
            prev.textContent.trim() === "Options:"
        ) {
            prev.remove();
        }
        wrap.remove();
    });
});
