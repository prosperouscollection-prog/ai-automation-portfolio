(function () {
  const data = {
    featuredOffers: [
      {
        id: "phone-coverage",
        icon: "📞",
        title: "Answer your phone when you cannot",
        description: "Riley answers calls after hours, during lunch, and while you are with customers. She can answer common questions and help book the next step.",
        fit: "Best first move for restaurants, salons, dental offices, HVAC teams, and any business that lives on phone calls.",
        price: "Starts at $1,500 setup + $300/month",
        demoHref: "/demos.html#demo-2",
        demoLabel: "Hear the phone demo",
        ctaLabel: "Book a call about missed calls"
      },
      {
        id: "lead-capture",
        icon: "🎯",
        title: "Reply to new leads in minutes",
        description: "When someone fills out your form or sends a message, they hear back fast. Hot leads get flagged so you can jump in when it matters most.",
        fit: "A strong first win for home services, real estate, recruiting, and any owner who loses leads overnight.",
        price: "Starts at $500 setup + $150/month",
        demoHref: "/demos.html#demo-1",
        demoLabel: "Watch the fast-reply demo",
        ctaLabel: "Book a call about faster follow-up"
      },
      {
        id: "website-helper",
        icon: "💬",
        title: "Answer the questions your team hears every day",
        description: "A website helper answers common questions about services, pricing, hours, and next steps using information from your business.",
        fit: "A simple first step for offices, retail stores, clinics, and service businesses that get the same questions again and again.",
        price: "Starts at $1,000 setup + $200/month",
        demoHref: "/demos.html#demo-3",
        demoLabel: "Try the website helper",
        ctaLabel: "Book a call about website questions"
      }
    ],
    offerLibrary: [
      {
        id: "never-miss-customer",
        icon: "🎯",
        title: "Never miss a customer again",
        description: "Fast replies for new inquiries so good leads do not go cold.",
        price: "$500 setup + $150/month",
        demoHref: "/demos.html#demo-1"
      },
      {
        id: "answer-phone",
        icon: "📞",
        title: "Answer your phone 24 hours a day",
        description: "Riley covers calls, answers questions, and helps book the next step.",
        price: "$1,500 setup + $300/month",
        demoHref: "/demos.html#demo-2"
      },
      {
        id: "website-faq",
        icon: "💬",
        title: "Answer customer questions 24/7",
        description: "A website helper answers common questions in plain English.",
        price: "$1,000 setup + $200/month",
        demoHref: "/demos.html#demo-3"
      },
      {
        id: "lead-sorting",
        icon: "⚡",
        title: "Sort, save, and follow up on new leads",
        description: "New forms get handled right away instead of sitting until morning.",
        price: "$2,000 setup + $400/month",
        demoHref: "/demos.html#demo-4"
      },
      {
        id: "trained-on-your-business",
        icon: "🧠",
        title: "Make it sound like your business",
        description: "Answers are trained on your menu, services, pricing, and tone.",
        price: "$5,000 setup + $500/month",
        demoHref: "/demos.html#demo-6"
      },
      {
        id: "watch-team",
        icon: "🛡️",
        title: "Have someone watching the moving parts",
        description: "Trendell gets a heads-up when something needs attention.",
        price: "$10,000 setup + $2,000/month",
        demoHref: "/demos.html#demo-8"
      },
      {
        id: "follow-up",
        icon: "⏱️",
        title: "Follow up before the lead forgets you",
        description: "Serious prospects hear back on time instead of falling through the cracks.",
        price: "$3,000 setup + $500/month",
        demoHref: "/demos.html#demo-1"
      },
      {
        id: "social-support",
        icon: "📱",
        title: "Keep your social posts moving",
        description: "Get post ideas, captions, and talking points without staring at a blank page.",
        price: "$2,000 setup + $400/month",
        demoHref: "/demos.html#demo-7"
      },
      {
        id: "client-check-ins",
        icon: "🤝",
        title: "Keep clients warm without chasing every update",
        description: "Routine check-ins, updates, and follow-ups happen on time.",
        price: "$2,500 setup + $500/month",
        demoHref: "/demos.html#demo-1"
      },
      {
        id: "phone-control",
        icon: "📲",
        title: "Check the basics from your phone",
        description: "Get quick updates without opening a laptop.",
        price: "$1,000 setup + $200/month",
        demoHref: "/demos.html#demo-8"
      },
      {
        id: "private-chat",
        icon: "💼",
        title: "Run key actions from one private chat",
        description: "See leads, results, and simple controls from one place on your phone.",
        price: "$1,000 setup + $200/month",
        demoHref: "/demos.html#demo-8"
      },
      {
        id: "content-builder",
        icon: "🎬",
        title: "Build a full post in under a minute",
        description: "Start with a topic and get talking points, a caption, and a post idea back fast.",
        price: "$1,500 setup + $300/month",
        demoHref: "/demos.html#demo-7"
      },
      {
        id: "new-customers",
        icon: "🔍",
        title: "Find new customers to reach out to",
        description: "Wake up to a tighter list of people worth contacting next.",
        price: "$2,000 setup + $400/month",
        demoHref: "/demos.html#demo-1"
      },
      {
        id: "full-business-stack",
        icon: "🚀",
        title: "Run the whole system together",
        description: "Calls, leads, website help, follow-up, content support, and oversight in one setup.",
        price: "$39,500 setup + $7,600/month",
        demoHref: "/demos.html"
      }
    ],
    demoHighlights: [
      {
        id: "demo-1",
        label: "Fast follow-up",
        title: "See how a new lead gets handled right away",
        description: "This shows the moment a new message comes in, gets sorted, and gets a fast reply.",
        problem: "Best when leads sit too long and cold traffic disappears overnight.",
        demoHref: "/demos.html#demo-1",
        demoLabel: "Open the lead demo",
        ctaLabel: "Book a call about lead capture"
      },
      {
        id: "demo-2",
        label: "Phone coverage",
        title: "Hear what callers hear when you cannot pick up",
        description: "Listen to Riley answer a call the way a real customer would hear it.",
        problem: "Best when phone calls are money and you cannot keep answering every one yourself.",
        demoHref: "/demos.html#demo-2",
        demoLabel: "Open the phone demo",
        ctaLabel: "Book a call about phone coverage"
      },
      {
        id: "demo-3",
        label: "Website helper",
        title: "Ask the questions your staff already answers every day",
        description: "Try common questions about services, pricing, hours, or next steps and see the reply.",
        problem: "Best when the same questions keep pulling you or your team away from paying work.",
        demoHref: "/demos.html#demo-3",
        demoLabel: "Open the website helper",
        ctaLabel: "Book a call about website questions"
      }
    ],
    pricingCards: [
      {
        id: "starter",
        name: "Starter",
        setup: "$500 one-time setup",
        monthly: "$150 per month after that",
        bestFor: "Businesses that want one clear first win without overbuilding.",
        features: [
          "One starting system built around your biggest leak",
          "Built and ready in 5 to 7 days",
          "Trendell oversees the setup personally",
          "Simple handoff and ongoing support"
        ],
        primaryLabel: "Book a Starter Call",
        secondaryType: "checkout",
        secondaryLabel: "Reserve Starter Setup — $500"
      },
      {
        id: "growth",
        name: "Growth",
        setup: "$3,500 one-time setup",
        monthly: "$650 per month after that",
        bestFor: "Businesses ready for phone coverage, lead capture, and follow-up together.",
        features: [
          "Riley answers your phone",
          "New leads get handled fast",
          "Weekly updates on what is coming in",
          "Same-day support when something needs attention"
        ],
        primaryLabel: "Book a Growth Planning Call",
        secondaryType: "consult",
        secondaryLabel: "Talk to Trendell first"
      },
      {
        id: "fullstack",
        name: "Full Stack",
        setup: "$39,500 one-time setup",
        monthly: "$7,600 per month after that",
        bestFor: "Businesses that want one operator-led system covering calls, leads, follow-up, and oversight.",
        features: [
          "Your core systems working together",
          "Trained on how your business actually works",
          "Daily visibility into what matters",
          "Direct founder oversight"
        ],
        primaryLabel: "Book a Full Stack Strategy Call",
        secondaryType: "consult",
        secondaryLabel: "Talk to Trendell first"
      }
    ],
    faqItems: [
      {
        question: "Do I need to know anything about technology?",
        answer: "No. You tell Trendell what is slowing you down, and Genesis AI Systems handles the setup, testing, and support."
      },
      {
        question: "What happens after I book a call?",
        answer: "You talk directly with Trendell. He will tell you what he would build first, what it would replace, and what the first week should look like."
      },
      {
        question: "Can I buy online without talking first?",
        answer: "Starter can be reserved online. For bigger builds, Trendell talks with you first so the setup fits your business and the scope is clear."
      },
      {
        question: "How fast can this be live?",
        answer: "Most first systems are ready in 5 to 7 days once the fit is clear and the business details are in hand."
      },
      {
        question: "What if something stops working?",
        answer: "That is part of the service. Trendell keeps an eye on the moving parts and fixes issues instead of leaving you to figure it out alone."
      }
    ]
  };

  window.GenesisHomepageData = data;
})();
