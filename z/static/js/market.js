async function fetchLiveMandiPrices() {
    const params = new URLSearchParams({
        state: "Maharashtra"
    });

    try {
        const response = await fetch(
            `/api/market/prices?${params.toString()}`,
            {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                }
            }
        );

        const data = await response.json();

        if (response.status === 401) {
            console.error("Login session expired.");
            window.location.href = "/login";
            return;
        }

        if (!response.ok || !data.success) {
            console.error("Mandi API error:", data);
            return;
        }

        console.log("Live Mandi record count:", data.count);
        console.log("Mandi prices:", data.prices);

        if (!data.prices || data.prices.length === 0) {
            console.warn("No live prices for the selected filters.");
            return;
        }

        // Pass actual API records to your existing UI renderer.
        // Example: renderMarketPrices(data.prices);

    } catch (error) {
        console.error("Mandi request failed:", error);
    }
}
 path