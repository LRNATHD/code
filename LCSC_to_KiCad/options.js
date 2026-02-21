function saveOptions(e) {
    e.preventDefault();
    const path = document.querySelector("#downloadPath").value || "KiCad_Imports";

    browser.storage.local.set({
        downloadPath: path
    });

    const status = document.getElementById("status");
    status.textContent = "Options saved.";
    status.style.display = "block";
    setTimeout(() => {
        status.style.display = "none";
    }, 1000);
}

function restoreOptions() {
    function setCurrentChoice(result) {
        document.querySelector("#downloadPath").value = result.downloadPath || "KiCad_Imports";
    }

    function onError(error) {
        console.log(`Error: ${error}`);
    }

    let getting = browser.storage.local.get("downloadPath");
    getting.then(setCurrentChoice, onError);
}

document.addEventListener("DOMContentLoaded", restoreOptions);
document.querySelector("#save").addEventListener("click", saveOptions);
