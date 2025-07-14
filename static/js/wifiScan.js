async function scanWifi() {
    try {
        await fetch('/wifi-scan')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById("ssid-list");
                console.log(list)
                list.innerHTML = "";
                data.networks.forEach(ssid => {
                    const option = document.createElement("option");
                    option.value = ssid;
                    list.appendChild(option);
                });
            });
    } catch (err) {
        console.log('Failed to load wifi', err)
    }
}

window.onload = () => {
    scanWifi();
};