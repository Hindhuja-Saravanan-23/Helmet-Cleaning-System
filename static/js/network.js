function checkNetworkStatus() {
    const status = navigator.onLine
        ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M4.91016 11.8396C9.21016 8.51961 14.8002 8.51961 19.1002 11.8396" stroke="#1F9A40" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M2 8.35961C8.06 3.67961 15.94 3.67961 22 8.35961" stroke="#1F9A40" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M6.79004 15.4902C9.94004 13.0502 14.05 13.0502 17.2 15.4902" stroke="#1F9A40" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M9.40039 19.1494C10.9804 17.9294 13.0304 17.9294 14.6104 19.1494" stroke="#1F9A40" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M4.91016 11.8396C9.21016 8.51961 14.8002 8.51961 19.1002 11.8396" stroke="#CE3737" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M2 8.35961C8.06 3.67961 15.94 3.67961 22 8.35961" stroke="#CE3737" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M6.79004 15.4902C9.94004 13.0502 14.05 13.0502 17.2 15.4902" stroke="#CE3737" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M9.40039 19.1494C10.9804 17.9294 13.0304 17.9294 14.6104 19.1494" stroke="#CE3737" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>`;

    document.getElementById("network_status").innerHTML = status;
    // if (navigator.onLine) document.getElementById("network_status").classList.add('pe-none');
}

window.addEventListener("online", checkNetworkStatus);
window.addEventListener("offline", checkNetworkStatus);
document.addEventListener("DOMContentLoaded", checkNetworkStatus);
