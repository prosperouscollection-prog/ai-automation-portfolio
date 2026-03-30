(function () {
  const runtime = window.GENESIS_RUNTIME_CONFIG || {};

  function validUrl(value) {
    if (!value || typeof value !== "string") return "";
    if (value.includes("[STRIPE_")) return "";
    if (value.includes("GA_MEASUREMENT_ID")) return "";
    return value.trim();
  }

  const config = {
    brand: {
      name: "Genesis AI Systems",
      founder: "Trendell Fordham",
      tagline: "Done-for-you AI automation for local businesses",
      location: "Detroit, MI"
    },
    contact: {
      phoneHref: "tel:+15866369550",
      phoneText: "(586) 636-9550",
      phonePlain: "586-636-9550",
      email: "info@genesisai.systems"
    },
    urls: {
      website: "https://genesisai.systems",
      demoServer: "https://genesis-ai-systems-demo.onrender.com",
      calendly: validUrl(runtime.calendlyUrl) || "https://calendly.com/genesisai-info-ptmt/free-ai-demo-call"
    },
    analytics: {
      googleMeasurementId: validUrl(runtime.googleMeasurementId || "")
    },
    checkout: {
      starter: {
        id: "starter",
        name: "Starter",
        amount: "$500",
        url: validUrl(runtime.stripeStarterLink) || "https://buy.stripe.com/4gM5kC0Vrfoj8LXfmX2Fa02",
        directCheckoutReady: true
      },
      growth: {
        id: "growth",
        name: "Growth",
        amount: "$3,500",
        url: validUrl(runtime.stripeGrowthLink || ""),
        directCheckoutReady: false
      },
      fullstack: {
        id: "fullstack",
        name: "Full Stack",
        amount: "$39,500",
        url: validUrl(runtime.stripeFullstackLink) || "https://buy.stripe.com/fZu14mcE9dgb9Q12Ab2Fa03",
        directCheckoutReady: true
      },
      deposit: {
        id: "deposit",
        name: "Build Deposit",
        amount: "$100",
        url: validUrl(runtime.stripeDepositLink) || "https://buy.stripe.com/4gM5kC0Vrfoj8LXfmX2Fa02",
        directCheckoutReady: true
      }
    }
  };

  window.GenesisSiteConfig = config;
})();
