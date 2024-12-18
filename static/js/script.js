document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll("input");

    inputs.forEach(input => {
        input.addEventListener("focus", () => {
            input.style.borderColor = "#6a11cb";
        });

        input.addEventListener("blur", () => {
            input.style.borderColor = "#2575fc";
        });
    });
});
