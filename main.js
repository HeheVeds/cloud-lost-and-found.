document.addEventListener("DOMContentLoaded", () => {
    // 1. Image Preview in Report Form
    const imageInput = document.getElementById("image");
    const imagePreviewContainer = document.getElementById("imagePreviewContainer");
    const imagePreview = document.getElementById("imagePreview");

    if (imageInput && imagePreviewContainer && imagePreview) {
        imageInput.addEventListener("change", function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.classList.remove("d-none");
                };
                reader.readAsDataURL(file);
            } else {
                imagePreviewContainer.classList.add("d-none");
                imagePreview.src = "";
            }
        });
    }

    // 2. Admin Key toggle in Registration Form
    const roleSelect = document.getElementById("roleSelect");
    const adminKeyField = document.getElementById("adminKeyField");

    if (roleSelect && adminKeyField) {
        roleSelect.addEventListener("change", function () {
            if (this.value === "admin") {
                adminKeyField.classList.remove("d-none");
                const input = adminKeyField.querySelector("input");
                if (input) input.setAttribute("required", "required");
            } else {
                adminKeyField.classList.add("d-none");
                const input = adminKeyField.querySelector("input");
                if (input) input.removeAttribute("required");
            }
        });
    }

    // 3. Auto dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll(".alert-dismissible");
        alerts.forEach((alert) => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        });
    }, 5000);
});
