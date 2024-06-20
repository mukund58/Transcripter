document.addEventListener("DOMContentLoaded", function() {
    const uploadForm = document.querySelector("form");
    uploadForm.addEventListener("submit", function() {
        const submitButton = document.querySelector("button");
        submitButton.innerHTML = "Uploading...";
        submitButton.disabled = true;
    });
});

