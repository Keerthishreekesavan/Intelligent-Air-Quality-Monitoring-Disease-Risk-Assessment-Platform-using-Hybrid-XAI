document.getElementById("prediction-form").addEventListener("submit", function(event) {
    event.preventDefault();

    let formData = {
        "CO": parseFloat(document.getElementById("CO").value),
        "NO": parseFloat(document.getElementById("NO").value),
        "NO2": parseFloat(document.getElementById("NO2").value),
        "O3": parseFloat(document.getElementById("O3").value),
        "SO2": parseFloat(document.getElementById("SO2").value),
        "PM2.5": parseFloat(document.getElementById("PM2.5").value),
        "PM10": parseFloat(document.getElementById("PM10").value),
        "NH3": parseFloat(document.getElementById("NH3").value)
    };

    fetch("/predict", {
        method: "POST",
        body: JSON.stringify(formData),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            document.getElementById("aqi-result").innerHTML = `AQI: ${data.AQI}`;
            document.getElementById("disease-result").innerHTML = `Disease Probabilities: ${data.Disease_Probabilities.map(p => p.toFixed(2)).join(", ")}`;
        }
    })
    .catch(error => console.error("Error:", error));
});
