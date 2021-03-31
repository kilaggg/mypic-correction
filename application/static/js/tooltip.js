function addTooltip(title, text, autoClose = false) {
    try {
        document.querySelector(".tooltip").remove();
    } catch (error) {
        
    }
    let tooltip = document.createElement("div");
    tooltip.classList.add("tooltip");
    document.body.appendChild(tooltip);

    let tooltipTitle = document.createElement("div");
    tooltipTitle.classList.add("tooltip-title");
    if (title != "") tooltipTitle.innerText = title;
    tooltip.appendChild(tooltipTitle);

    let tooltipBody = document.createElement("div");
    tooltipBody.classList.add("tooltip-body");
    if (text != "" && text != undefined) tooltipBody.innerText = text;
    tooltip.appendChild(tooltipBody);

    if (autoClose) {
        setTimeout(() => {
            tooltip.remove();
        }, 2600);
    } else {
        let closeButton = document.createElement("button");
        closeButton.innerText = "X";
        tooltipTitle.appendChild(closeButton);

        closeButton
            .addEventListener("click", () => {
            tooltip.remove();
        });
    }
}