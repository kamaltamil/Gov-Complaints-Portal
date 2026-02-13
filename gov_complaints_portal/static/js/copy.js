(function () {
    function showCopiedToast() {
        var toastEl = document.getElementById("copyToast");
        if (!toastEl || typeof bootstrap === "undefined") {
            return;
        }
        var toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 1500 });
        toast.show();
    }

    async function copyText(value) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(value);
            return;
        }
        var tempInput = document.createElement("input");
        tempInput.value = value;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand("copy");
        document.body.removeChild(tempInput);
    }

    document.addEventListener("DOMContentLoaded", function () {
        var buttons = document.querySelectorAll(".js-copy-btn");
        buttons.forEach(function (button) {
            button.addEventListener("click", async function () {
                try {
                    var textToCopy = button.dataset.copyText || "";
                    if (button.dataset.copyUrl) {
                        textToCopy = window.location.href;
                    }
                    if (!textToCopy) {
                        return;
                    }
                    await copyText(textToCopy);
                    showCopiedToast();
                } catch (error) {
                    console.error("Copy failed:", error);
                }
            });
        });
    });
})();
