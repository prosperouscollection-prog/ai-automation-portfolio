(function () {
  const fallbackConfig = {
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
      calendly: "https://calendly.com/genesisai-info-ptmt/free-ai-demo-call"
    },
    analytics: {
      googleMeasurementId: ""
    },
    checkout: {
      starter: {
        id: "starter",
        name: "Starter",
        amount: "$500",
        url: "https://buy.stripe.com/4gM5kC0Vrfoj8LXfmX2Fa02",
        directCheckoutReady: true
      },
      growth: {
        id: "growth",
        name: "Growth",
        amount: "$3,500",
        url: "",
        directCheckoutReady: false
      },
      deposit: {
        id: "deposit",
        name: "Build Deposit",
        amount: "$100",
        url: "https://buy.stripe.com/4gM5kC0Vrfoj8LXfmX2Fa02",
        directCheckoutReady: true
      }
    }
  };

  const config = window.GenesisSiteConfig || fallbackConfig;
  let analyticsLoaded = false;

  const sectionRouteMap = {
    how: { label: "How It Works", homeHref: "#how-it-works", otherHref: "/#how-it-works" },
    examples: { label: "Real Examples", homeHref: "#examples", otherHref: "/#examples" },
    about: { label: "About", href: "/about.html" },
    demos: { label: "Demos", href: "/demos.html" },
    pricing: { label: "Pricing", homeHref: "#pricing", otherHref: "/#pricing" },
    dashboard: { label: "Dashboard", href: "/dashboard.html" },
    contact: { label: "Contact", homeHref: "#contact", otherHref: "/#contact" }
  };

  function isHomePage() {
    const path = window.location.pathname;
    return path === "/" || path.endsWith("/index.html");
  }

  function navHref(key) {
    const item = sectionRouteMap[key];
    if (item.href) return item.href;
    return isHomePage() ? item.homeHref : item.otherHref;
  }

  function activePathKey(page) {
    if (page === "about") return "about";
    if (page === "demos") return "demos";
    if (page === "dashboard" || page === "client-dashboard") return "dashboard";
    if (page === "contact") return "contact";
    return "";
  }

  function logoMarkup() {
    return `
      <svg id="genesis-logo" viewBox="0 0 200 40" xmlns="http://www.w3.org/2000/svg" width="160" height="32" aria-hidden="true">
        <circle cx="16" cy="20" r="14" fill="none" stroke="#2563eb" stroke-width="1.5"></circle>
        <path d="M16 6 A14 14 0 1 0 28 13" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round"></path>
        <circle cx="16" cy="6" r="2.5" fill="#2563eb"></circle>
        <path d="M22 16 L10 16 A8 8 0 1 1 22 24 L22 20 L14 20" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
        <text x="38" y="15" font-family="system-ui,sans-serif" font-size="13" font-weight="600" fill="white">GENESIS AI</text>
        <text x="38" y="29" font-family="system-ui,sans-serif" font-size="10" font-weight="400" fill="#2563eb" letter-spacing="2">SYSTEMS</text>
      </svg>
    `;
  }

  function buildShellMarkup(options) {
    const activeKey = activePathKey(options.page || "");
    const navLinks = ["how", "examples", "about", "demos", "pricing", "contact"]
      .map((key) => {
        const item = sectionRouteMap[key];
        const active = activeKey === key ? "active" : "";
        return `<a class="nav-link ${active}" data-nav-key="${key}" href="${navHref(key)}">${item.label}</a>`;
      })
      .join("");

    const footerLinks = `
      <a href="/">Home</a>
      <a href="/about.html">About</a>
      <a href="/demos.html">Demos</a>
      <a href="/#pricing">Pricing</a>
      <a href="/dashboard.html">Dashboard</a>
      <a href="/command.html">Command Center</a>
      <a href="/privacy-policy.html">Privacy Policy</a>
      <a href="/terms.html">Terms of Service</a>
    `;

    return {
      nav: `
        <a class="skip-link" href="#main-content">Skip to main content</a>
        <nav class="site-nav" aria-label="Main navigation">
          <div class="shell nav-inner">
            <a class="brand-link" href="/" aria-label="${config.brand.name} home">
              ${logoMarkup()}
            </a>
            <div class="nav-links">
              ${navLinks}
            </div>
            <div class="nav-actions">
              <a
                class="button button-primary nav-cta"
                href="${config.urls.calendly}"
                target="_blank"
                rel="noreferrer"
                data-track-event="nav_primary_cta_click"
                data-track-location="nav"
              >Book a Free Call</a>
              <button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">
                <span></span><span></span><span></span>
              </button>
            </div>
          </div>
        </nav>
        <div class="mobile-overlay" id="mobileMenu" aria-hidden="true">
          <div class="mobile-menu">
            <div class="mobile-menu-top">
              <a class="brand-link" href="/" aria-label="${config.brand.name} home">
                ${logoMarkup()}
              </a>
              <button class="mobile-close" id="mobileClose" aria-label="Close menu">✕</button>
            </div>
            <div class="mobile-links">
              <a href="${navHref("how")}">How It Works</a>
              <a href="${navHref("examples")}">Real Examples</a>
              <a href="/about.html">About</a>
              <a href="/demos.html">Demos</a>
              <a href="${navHref("pricing")}">Pricing</a>
              <a href="${navHref("contact")}">Contact</a>
              <a
                class="button button-primary"
                href="${config.urls.calendly}"
                target="_blank"
                rel="noreferrer"
                data-track-event="mobile_nav_primary_cta_click"
                data-track-location="mobile-nav"
              >Book a Free Call</a>
            </div>
          </div>
        </div>
      `,
      footer: `
        <footer class="site-footer">
          <div class="shell">
            <div class="footer-grid">
              <div class="footer-brand">
                <a class="brand-link" href="/" aria-label="${config.brand.name} home">
                  ${logoMarkup()}
                </a>
                <p>${config.brand.tagline}</p>
                <p>Built in ${config.brand.location}</p>
              </div>
              <div>
                <h3 class="footer-links-title">Quick Links</h3>
                <div class="footer-links-list">
                  ${footerLinks}
                </div>
              </div>
              <div class="footer-contact">
                <h3 class="footer-contact-title">Contact Us</h3>
                <p>📞 <a href="${config.contact.phoneHref}">${config.contact.phoneText}</a></p>
                <p>Riley answers 24/7</p>
                <p>📧 <a href="mailto:${config.contact.email}">${config.contact.email}</a></p>
                <p>📅 <a href="${config.urls.calendly}" target="_blank" rel="noreferrer">Book a free call</a></p>
              </div>
            </div>
            <div class="footer-bottom">
              <div>© 2026 ${config.brand.name} | ${config.brand.location} | All Rights Reserved</div>
              <div>14 AI Systems | 11 Agents Running 24/7</div>
            </div>
          </div>
        </footer>
      `,
      sticky: `
        <div class="mobile-sticky" id="mobileSticky">
          <a
            class="button button-primary"
            href="${config.urls.calendly}"
            target="_blank"
            rel="noreferrer"
            data-track-event="sticky_primary_cta_click"
            data-track-location="mobile-sticky"
          >Book a Free Call</a>
          <a
            class="button button-outline"
            href="${navHref("pricing")}"
            data-track-event="sticky_secondary_cta_click"
            data-track-location="mobile-sticky"
          >See Pricing</a>
        </div>
      `,
      chat: `
        <div class="chat-hint" id="chatHint">👋 Hi! Have questions about your business? I am here to help.</div>
        <button class="chat-launcher" id="chatLauncher" aria-label="Open chat">💬</button>
        <div class="chat-window" id="chatWindow">
          <div class="chat-head">
            <div>
              <strong>${config.brand.name}</strong>
              <span>Ask about your business any time</span>
            </div>
            <button class="mobile-close" id="chatClose" aria-label="Close chat">✕</button>
          </div>
          <div class="chat-log" id="chatLog" aria-live="polite">
            <div class="chat-bubble bot">Hi! Tell me what kind of business you run and what is eating your time right now.</div>
          </div>
          <form class="chat-form" id="chatForm">
            <input id="chatInput" type="text" placeholder="Type your question" aria-label="Message Genesis AI Systems chat">
            <button class="button button-primary" type="submit">Send</button>
          </form>
        </div>
      `,
      exit: `
        <div class="exit-overlay" id="exitOverlay" aria-hidden="true">
          <div class="exit-modal" role="dialog" aria-modal="true" aria-labelledby="exitTitle">
            <button class="exit-close" id="exitClose" aria-label="Close popup">✕</button>
            <h3 id="exitTitle">Before you go</h3>
            <p>Leave your email and Trendell will send the next best step for your business.</p>
            <form id="exitForm" class="contact-form">
              <label>
                Email address
                <input id="exitEmail" type="email" required placeholder="you@yourbusiness.com">
              </label>
              <button class="button button-primary full" type="submit">Get My Free Recommendation</button>
            </form>
          </div>
        </div>
      `
    };
  }

  function mountShell(options) {
    const markup = buildShellMarkup(options || {});
    const navMount = document.getElementById("siteNavMount");
    const footerMount = document.getElementById("siteFooterMount");
    const stickyMount = document.getElementById("siteStickyMount");
    const chatMount = document.getElementById("siteChatMount");
    const exitMount = document.getElementById("siteExitMount");

    if (navMount) navMount.innerHTML = markup.nav;
    if (footerMount) footerMount.innerHTML = markup.footer;
    if (stickyMount && options.stickyBar) stickyMount.innerHTML = markup.sticky;
    if (chatMount && options.chat) chatMount.innerHTML = markup.chat;
    if (exitMount && options.exitModal) exitMount.innerHTML = markup.exit;
  }

  function loadAnalytics() {
    const measurementId = config.analytics.googleMeasurementId;
    if (!measurementId || analyticsLoaded || typeof document === "undefined") return;
    analyticsLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag("js", new Date());
    window.gtag("config", measurementId);

    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
    document.head.appendChild(script);
  }

  function trackEvent(name, payload) {
    if (!config.analytics.googleMeasurementId) return;
    loadAnalytics();
    if (typeof window.gtag === "function") {
      window.gtag("event", name, payload || {});
    }
  }

  function setActiveNav(sectionKey) {
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.toggle("active", link.dataset.navKey === sectionKey);
    });
  }

  function initMenu() {
    const toggle = document.getElementById("navToggle");
    const overlay = document.getElementById("mobileMenu");
    const close = document.getElementById("mobileClose");
    if (!toggle || !overlay || !close) return;

    const open = () => {
      overlay.classList.add("open");
      overlay.setAttribute("aria-hidden", "false");
      toggle.setAttribute("aria-expanded", "true");
      document.body.classList.add("no-scroll");
    };

    const shut = () => {
      overlay.classList.remove("open");
      overlay.setAttribute("aria-hidden", "true");
      toggle.setAttribute("aria-expanded", "false");
      document.body.classList.remove("no-scroll");
    };

    toggle.addEventListener("click", open);
    close.addEventListener("click", shut);
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) shut();
    });
    overlay.querySelectorAll("a").forEach((link) => link.addEventListener("click", shut));
  }

  function initHomeNavObserver() {
    if (!isHomePage()) return;
    const targets = [
      { id: "how-it-works", key: "how" },
      { id: "examples", key: "examples" },
      { id: "pricing", key: "pricing" },
      { id: "contact", key: "contact" }
    ];

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (!visible) return;
        const match = targets.find((item) => item.id === visible.target.id);
        if (match) setActiveNav(match.key);
      },
      { threshold: [0.2, 0.45, 0.7], rootMargin: "-30% 0px -45% 0px" }
    );

    targets.forEach((item) => {
      const element = document.getElementById(item.id);
      if (element) observer.observe(element);
    });
  }

  function addBubble(log, text, type) {
    const item = document.createElement("div");
    item.className = `chat-bubble ${type}`;
    item.textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  }

  async function askChat(message) {
    const response = await fetch(`${config.urls.demoServer}/demo/rag-chatbot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: message })
    });
    const data = await response.json();
    return data.answer || data.message || "I can help with that.";
  }

  function initChat() {
    const launcher = document.getElementById("chatLauncher");
    const windowEl = document.getElementById("chatWindow");
    const close = document.getElementById("chatClose");
    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");
    const log = document.getElementById("chatLog");
    const hint = document.getElementById("chatHint");
    if (!launcher || !windowEl || !close || !form || !input || !log) return;

    let opened = false;

    const open = () => {
      opened = true;
      launcher.classList.remove("pulse");
      if (hint) hint.classList.remove("show");
      windowEl.classList.add("open");
      trackEvent("chat_widget_open", { location: window.location.pathname });
    };

    const shut = () => {
      windowEl.classList.remove("open");
    };

    launcher.addEventListener("click", () => {
      if (windowEl.classList.contains("open")) {
        shut();
      } else {
        open();
      }
    });

    close.addEventListener("click", shut);

    setTimeout(() => {
      if (!opened) launcher.classList.add("pulse");
    }, 30000);

    setTimeout(() => {
      if (!opened && hint) {
        hint.classList.add("show");
        setTimeout(() => hint.classList.remove("show"), 8000);
      }
    }, 45000);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      addBubble(log, message, "user");
      input.value = "";
      try {
        const answer = await askChat(message);
        addBubble(log, answer, "bot");
      } catch (error) {
        addBubble(log, "I hit a snag. Please call us or book a free call and Trendell will help.", "bot");
      }
    });
  }

  function initStickyBar() {
    const sticky = document.getElementById("mobileSticky");
    if (!sticky) return;

    const update = () => {
      const show = window.innerWidth < 768 && window.scrollY > 400;
      sticky.classList.toggle("show", show);
      document.body.classList.toggle("sticky-visible", show);
    };

    update();
    window.addEventListener("scroll", update);
    window.addEventListener("resize", update);
  }

  function initExitModal() {
    const overlay = document.getElementById("exitOverlay");
    const close = document.getElementById("exitClose");
    const form = document.getElementById("exitForm");
    const email = document.getElementById("exitEmail");
    if (!overlay || !close || !form || !email) return;

    let shown = false;

    const open = () => {
      shown = true;
      overlay.classList.add("show");
      overlay.setAttribute("aria-hidden", "false");
      document.body.classList.add("no-scroll");
      email.focus();
      trackEvent("exit_intent_popup_open", { location: window.location.pathname });
    };

    const shut = () => {
      overlay.classList.remove("show");
      overlay.setAttribute("aria-hidden", "true");
      document.body.classList.remove("no-scroll");
    };

    close.addEventListener("click", shut);
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) shut();
    });

    document.addEventListener("mouseout", (event) => {
      if (shown || window.innerWidth < 768 || window.scrollY < 220) return;
      if (event.clientY <= 24) open();
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = email.value.trim();
      if (!value) return;
      localStorage.setItem("genesis_exit_email", value);
      trackEvent("exit_intent_popup_submit", {
        location: window.location.pathname
      });
      shut();
      const contact = document.getElementById("contact");
      if (contact) {
        contact.scrollIntoView({ behavior: "smooth", block: "start" });
        const contactEmail = document.querySelector('input[name="email"]');
        if (contactEmail && !contactEmail.value) contactEmail.value = value;
      } else {
        window.location.href = "/#contact";
      }
    });
  }

  function activateTab(group, nextButton) {
    const buttons = group.querySelectorAll("[data-tab-target]");
    const panels = document.querySelectorAll(`[data-tab-panel="${group.dataset.tabGroup}"]`);

    buttons.forEach((button) => {
      const active = button === nextButton;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
      button.tabIndex = active ? 0 : -1;
    });

    panels.forEach((panel) => {
      const active = panel.id === nextButton.dataset.tabTarget;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  }

  function initTabs() {
    document.querySelectorAll("[data-tab-group]").forEach((group) => {
      const buttons = Array.from(group.querySelectorAll("[data-tab-target]"));
      if (!buttons.length) return;

      buttons.forEach((button, index) => {
        button.setAttribute("role", "tab");
        button.setAttribute("aria-selected", button.classList.contains("active") ? "true" : "false");
        button.tabIndex = button.classList.contains("active") ? 0 : -1;
        const panel = document.getElementById(button.dataset.tabTarget);
        if (panel) {
          panel.setAttribute("role", "tabpanel");
          panel.hidden = !button.classList.contains("active");
        }

        button.addEventListener("click", () => activateTab(group, button));
        button.addEventListener("keydown", (event) => {
          if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
          event.preventDefault();

          let nextIndex = index;
          if (event.key === "ArrowRight") nextIndex = (index + 1) % buttons.length;
          if (event.key === "ArrowLeft") nextIndex = (index - 1 + buttons.length) % buttons.length;
          if (event.key === "Home") nextIndex = 0;
          if (event.key === "End") nextIndex = buttons.length - 1;

          const nextButton = buttons[nextIndex];
          activateTab(group, nextButton);
          nextButton.focus();
        });
      });
    });
  }

  function initFaq() {
    document.querySelectorAll(".faq-item").forEach((item) => {
      const button = item.querySelector(".faq-question");
      if (!button) return;
      button.addEventListener("click", () => {
        item.classList.toggle("open");
        button.setAttribute("aria-expanded", item.classList.contains("open") ? "true" : "false");
      });
    });
  }

  function responseByBusiness(type) {
    const value = (type || "").toLowerCase();
    if (value.includes("restaurant")) return "We will likely start with after-hours calls, reservations, and menu questions so you stop losing busy-night business.";
    if (value.includes("dental")) return "We will likely start with new patient calls, insurance questions, and after-hours booking so your front desk gets breathing room.";
    if (value.includes("hvac")) return "We will likely start with fast replies for emergency jobs so the hot calls reach you before a competitor does.";
    if (value.includes("salon")) return "We will likely start with round-the-clock booking and no-show reminders so your chairs stay full.";
    if (value.includes("real estate")) return "We will likely start with fast replies to showing requests so serious buyers hear from you first.";
    if (value.includes("retail")) return "We will likely start with a website helper that answers product and return questions right away.";
    return "We will look at the biggest leak in your business first and tell you what to build before you spend a dollar.";
  }

  async function postContact(payload) {
    try {
      const localResponse = await fetch("/submit/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (localResponse.ok) return await localResponse.json();
    } catch (error) {
      // Try the fallback demo server next.
    }

    const fallback = await fetch(`${config.urls.demoServer}/submit/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    return await fallback.json();
  }

  function setFormResponse(node, type, message) {
    if (!node) return;
    node.classList.add("show");
    node.dataset.status = type;
    node.textContent = message;
  }

  function initContactForm() {
    const form = document.getElementById("contactForm");
    const response = document.getElementById("contactResponse");
    if (!form || !response) return;

    const storedEmail = localStorage.getItem("genesis_exit_email");
    const emailField = form.querySelector('input[name="email"]');
    if (storedEmail && emailField && !emailField.value) {
      emailField.value = storedEmail;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const payload = {
        name: String(data.get("name") || "").trim(),
        business: String(data.get("business") || "").trim(),
        phone: String(data.get("phone") || "").trim(),
        email: String(data.get("email") || "").trim(),
        business_type: String(data.get("business_type") || "").trim(),
        pain_point: String(data.get("pain_point") || "").trim()
      };

      const requiredFields = ["name", "business", "phone", "email"];
      let hasError = false;
      requiredFields.forEach((fieldName) => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        const missing = !payload[fieldName];
        if (field) {
          field.toggleAttribute("aria-invalid", missing);
        }
        hasError = hasError || missing;
      });

      if (hasError) {
        setFormResponse(response, "error", "Please fill in your name, business, phone number, and email address so Trendell can reach you.");
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      const originalText = submitButton ? submitButton.textContent : "";
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Sending your note...";
      }

      try {
        const result = await postContact(payload);
        const personalized = result.message || responseByBusiness(payload.business_type);
        setFormResponse(response, "success", `${personalized} Trendell will reach out within 24 hours. Sending you to the next step now.`);
        trackEvent("contact_form_submit", {
          business_type: payload.business_type || "unknown",
          location: window.location.pathname
        });
        setTimeout(() => {
          window.location.href = "/thank-you.html";
        }, 3000);
      } catch (error) {
        setFormResponse(response, "error", "Your note is ready. If the form stalls, call us or book your free call and Trendell will take it from there.");
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalText || "Get My Free Recommendation";
        }
      }
    });
  }

  async function initActivity() {
    const leadsCount = document.getElementById("leadsTodayCount");
    const demosCount = document.getElementById("demosTodayCount");
    const feed = document.getElementById("activityFeed");
    if (!leadsCount && !demosCount && !feed) return;

    try {
      const [leadRes, demoRes, activityRes] = await Promise.all([
        fetch(`${config.urls.demoServer}/stats/leads-today`),
        fetch(`${config.urls.demoServer}/stats/demos`),
        fetch(`${config.urls.demoServer}/stats/recent-activity`)
      ]);

      if (leadRes.ok && leadsCount) {
        const data = await leadRes.json();
        leadsCount.textContent = data.count || 0;
      }

      if (demoRes.ok && demosCount) {
        const data = await demoRes.json();
        demosCount.textContent = data.count || 0;
      }

      if (activityRes.ok && feed) {
        const data = await activityRes.json();
        const items = (data.items || []).slice(0, 5);
        if (!items.length) {
          feed.innerHTML = '<p class="small-note">Live example data is not available right now. Trendell can walk you through it on the call.</p>';
          return;
        }

        feed.innerHTML = items
          .map((item) => {
            const text = typeof item === "string" ? item : item.text;
            return `
              <div class="activity-item">
                <span class="activity-dot"></span>
                <span>${text}</span>
              </div>
            `;
          })
          .join("");
      }
    } catch (error) {
      if (feed) {
        feed.innerHTML = '<p class="small-note">Live example data is not available right now. Trendell can show you how it works on the call.</p>';
      }
    }
  }

  function initClickTracking() {
    document.addEventListener("click", (event) => {
      const target = event.target.closest("a, button");
      if (!target) return;

      const explicitEvent = target.dataset.trackEvent;
      if (explicitEvent) {
        trackEvent(explicitEvent, {
          location: target.dataset.trackLocation || window.location.pathname,
          label: target.dataset.trackLabel || target.textContent.trim()
        });
      }

      if (target.tagName === "A") {
        const href = target.getAttribute("href") || "";
        if (href.includes("calendly.com")) {
          trackEvent("calendly_click", {
            location: target.dataset.trackLocation || window.location.pathname,
            label: target.dataset.trackLabel || target.textContent.trim()
          });
        }
        if (href.includes("buy.stripe.com")) {
          trackEvent("stripe_checkout_click", {
            location: target.dataset.trackLocation || window.location.pathname,
            label: target.dataset.trackLabel || target.textContent.trim()
          });
        }
      }
    });
  }

  function initCommon() {
    loadAnalytics();
    initMenu();
    initHomeNavObserver();
    initTabs();
    initFaq();
    initStickyBar();
    initChat();
    initExitModal();
    initContactForm();
    initActivity();
    initClickTracking();
  }

  window.GenesisSite = {
    config,
    mountShell,
    initCommon,
    initTabs,
    initFaq,
    initActivity,
    initContactForm,
    askChat,
    trackEvent
  };
})();
