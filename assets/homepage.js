(function () {
  const site = window.GenesisSite || {};
  const config = window.GenesisSiteConfig || site.config || {};
  const data = window.GenesisHomepageData || {};

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function consultHref() {
    return (config.urls && config.urls.calendly) || "#contact";
  }

  function checkoutFor(planId) {
    return (config.checkout && config.checkout[planId]) || null;
  }

  function featuredOfferMarkup(item) {
    return `
      <article class="feature-card">
        <div class="icon">${escapeHtml(item.icon)}</div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.description)}</p>
        <p class="small-note" style="margin-top:14px;">${escapeHtml(item.fit)}</p>
        <div class="price-pill">${escapeHtml(item.price)}</div>
        <div class="card-actions">
          <a
            class="button button-outline"
            href="${escapeHtml(item.demoHref)}"
            data-track-event="featured_offer_demo_click"
            data-track-location="homepage-featured-offers"
            data-track-label="${escapeHtml(item.title)}"
          >${escapeHtml(item.demoLabel)}</a>
          <a
            class="button button-primary"
            href="${escapeHtml(consultHref())}"
            target="_blank"
            rel="noreferrer"
            data-track-event="featured_offer_consult_click"
            data-track-location="homepage-featured-offers"
            data-track-label="${escapeHtml(item.title)}"
          >${escapeHtml(item.ctaLabel)}</a>
        </div>
      </article>
    `;
  }

  function offerLibraryMarkup(item) {
    return `
      <article class="compact-offer-card">
        <div class="compact-offer-head">
          <span class="compact-offer-icon">${escapeHtml(item.icon)}</span>
          <div>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.description)}</p>
          </div>
        </div>
        <div class="compact-offer-footer">
          <span class="small-pill">${escapeHtml(item.price)}</span>
          <div class="button-row compact-offer-actions">
            <a
              class="button button-outline"
              href="${escapeHtml(item.demoHref)}"
              data-track-event="offer_library_demo_click"
              data-track-location="homepage-offer-library"
              data-track-label="${escapeHtml(item.title)}"
            >See example</a>
            <a
              class="button button-soft"
              href="${escapeHtml(consultHref())}"
              target="_blank"
              rel="noreferrer"
              data-track-event="offer_library_consult_click"
              data-track-location="homepage-offer-library"
              data-track-label="${escapeHtml(item.title)}"
            >Talk to Trendell first</a>
          </div>
        </div>
      </article>
    `;
  }

  function demoHighlightMarkup(item) {
    return `
      <article class="demo-preview-card">
        <div class="label">${escapeHtml(item.label)}</div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="demo-note">${escapeHtml(item.description)}</p>
        <div class="demo-cta">
          <p>${escapeHtml(item.problem)}</p>
          <div class="button-row">
            <a
              class="button button-outline"
              href="${escapeHtml(item.demoHref)}"
              data-track-event="demo_cta_click"
              data-track-location="homepage-demos"
              data-track-label="${escapeHtml(item.title)}"
            >${escapeHtml(item.demoLabel)}</a>
            <a
              class="button button-primary"
              href="${escapeHtml(consultHref())}"
              target="_blank"
              rel="noreferrer"
              data-track-event="demo_consult_click"
              data-track-location="homepage-demos"
              data-track-label="${escapeHtml(item.title)}"
            >${escapeHtml(item.ctaLabel)}</a>
          </div>
        </div>
      </article>
    `;
  }

  function pricingCardMarkup(item, index) {
    const checkout = checkoutFor(item.id);
    const isFeatured = index === 0 ? " featured" : "";
    const featuredBadge = index === 0 ? '<div class="pricing-badge">Best first step</div>' : "";

    let secondaryAction = "";
    if (item.secondaryType === "checkout" && checkout && checkout.directCheckoutReady && checkout.url) {
      secondaryAction = `
        <a
          class="button button-outline"
          href="${escapeHtml(checkout.url)}"
          target="_blank"
          rel="noreferrer"
          data-track-event="pricing_checkout_click"
          data-track-location="homepage-pricing"
          data-track-label="${escapeHtml(item.name)}"
        >${escapeHtml(item.secondaryLabel)}</a>
      `;
    } else {
      secondaryAction = `
        <a
          class="button button-outline"
          href="${escapeHtml(consultHref())}"
          target="_blank"
          rel="noreferrer"
          data-track-event="pricing_secondary_cta_click"
          data-track-location="homepage-pricing"
          data-track-label="${escapeHtml(item.name)}"
        >${escapeHtml(item.secondaryLabel)}</a>
      `;
    }

    return `
      <article class="pricing-card${isFeatured}">
        ${featuredBadge}
        <h3>${escapeHtml(item.name)}</h3>
        <p class="price-amount">${escapeHtml(item.setup)}</p>
        <p class="price-line">${escapeHtml(item.monthly)}</p>
        <p><strong>Best for:</strong> ${escapeHtml(item.bestFor)}</p>
        <div class="feature-list">
          ${item.features.map((feature) => `<div>• ${escapeHtml(feature)}</div>`).join("")}
        </div>
        <div class="button-row" style="margin-top:auto;">
          <a
            class="button button-primary"
            href="${escapeHtml(consultHref())}"
            target="_blank"
            rel="noreferrer"
            data-track-event="pricing_primary_cta_click"
            data-track-location="homepage-pricing"
            data-track-label="${escapeHtml(item.name)}"
          >${escapeHtml(item.primaryLabel)}</a>
          ${secondaryAction}
        </div>
      </article>
    `;
  }

  function faqMarkup(item) {
    return `
      <article class="faq-item">
        <button class="faq-question" type="button" aria-expanded="false">
          <span>${escapeHtml(item.question)}</span>
          <span>+</span>
        </button>
        <div class="faq-answer">
          <p>${escapeHtml(item.answer)}</p>
        </div>
      </article>
    `;
  }

  function renderSection(mountId, list, mapper) {
    const mount = document.getElementById(mountId);
    if (!mount || !Array.isArray(list)) return;
    mount.innerHTML = list.map(mapper).join("");
  }

  function init() {
    renderSection("featuredOffersMount", data.featuredOffers, featuredOfferMarkup);
    renderSection("offerLibraryMount", data.offerLibrary, offerLibraryMarkup);
    renderSection("demoHighlightsMount", data.demoHighlights, demoHighlightMarkup);
    renderSection("pricingCardsMount", data.pricingCards, pricingCardMarkup);
    renderSection("pricingFaqMount", data.faqItems, faqMarkup);
  }

  window.GenesisHomepage = {
    init
  };
})();
