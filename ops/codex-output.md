completed	failure	codex: remove P16 validation dispatch	QA Agent - Genesis AI Systems	main	push	23990211145	10s	2026-04-04T23:53:03Z
qa-check	Check key pages return 200	2026-04-04T23:53:10.0646058Z https://genesisai.systems/demos.html -> 200
qa-check	Check key pages return 200	2026-04-04T23:53:10.1326472Z https://genesisai.systems/sitemap.xml -> 200
qa-check	Check key pages return 200	2026-04-04T23:53:10.2089194Z https://genesisai.systems/robots.txt -> 200
qa-check	Check homepage CRO sections and form	﻿2026-04-04T23:53:10.2123122Z ##[group]Run PAGE=$(curl -sL --max-time 30 https://genesisai.systems)
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2123751Z [36;1mPAGE=$(curl -sL --max-time 30 https://genesisai.systems)[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2124151Z [36;1mecho "$PAGE" | grep -q 'id="contactForm"'[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2124536Z [36;1mecho "$PAGE" | grep -q 'Most businesses start with one clear fix'[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2124983Z [36;1mecho "$PAGE" | grep -q 'Why owners feel safe starting here'[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2125369Z [36;1mecho "$PAGE" | grep -q 'What you see after launch'[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2125779Z [36;1mecho "$PAGE" | grep -q 'Tell Trendell what is slowing the business down'[0m
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2152883Z shell: /usr/bin/bash -e {0}
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2153133Z ##[endgroup]
qa-check	Check homepage CRO sections and form	2026-04-04T23:53:10.2817402Z ##[error]Process completed with exit code 1.
qa-check	Telegram alert on failure	﻿2026-04-04T23:53:10.2974207Z ##[group]Run pip install requests -q
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2974600Z [36;1mpip install requests -q[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2974886Z [36;1mpython3 - << 'PYEOF'[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2975124Z [36;1mimport os, requests[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2975390Z [36;1mtoken = os.getenv('TELEGRAM_BOT_TOKEN', '')[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2975714Z [36;1mchat = os.getenv('TELEGRAM_CHAT_ID', '')[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2976693Z [36;1mmsg = "🚨 QA Agent FAILED\nA site check failed.\nCheck GitHub Actions:\ngithub.com/prosperouscollection-prog/ai-automation-portfolio/actions"[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2977364Z [36;1mif token and chat:[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2977575Z [36;1m    try:[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2977922Z [36;1m        r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2978389Z [36;1m            json={'chat_id': chat, 'text': msg}, timeout=10)[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2978840Z [36;1m        print('✅ Telegram alert sent' if r.ok else f'⚠️ Telegram {r.status_code}')[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2979281Z [36;1m    except Exception as e:[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2979547Z [36;1m        print(f'⚠️ Telegram failed: {e}')[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.2979806Z [36;1mPYEOF[0m
qa-check	Telegram alert on failure	2026-04-04T23:53:10.3006793Z shell: /usr/bin/bash -e {0}
qa-check	Telegram alert on failure	2026-04-04T23:53:10.3007039Z env:
qa-check	Telegram alert on failure	2026-04-04T23:53:10.3007552Z   TELEGRAM_BOT_TOKEN: ***
qa-check	Telegram alert on failure	2026-04-04T23:53:10.3007807Z   TELEGRAM_CHAT_ID: ***
qa-check	Telegram alert on failure	2026-04-04T23:53:10.3008011Z ##[endgroup]
qa-check	Telegram alert on failure	2026-04-04T23:53:11.9265962Z ✅ Telegram alert sent
qa-check	Post Run actions/checkout@v4	﻿2026-04-04T23:53:11.9512917Z Post job cleanup.
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0443447Z [command]/usr/bin/git version
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0479904Z git version 2.53.0
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0523699Z Temporarily overriding HOME='/home/runner/work/_temp/96feb543-e39a-49b4-b7f8-c746f0c9fa01' before making global git config changes
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0524512Z Adding repository directory to the temporary git global config as a safe directory
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0530873Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/ai-automation-portfolio/ai-automation-portfolio
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0573968Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0606477Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0844892Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0866637Z http.https://github.com/.extraheader
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0879010Z [command]/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.0908990Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.1136369Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:
qa-check	Post Run actions/checkout@v4	2026-04-04T23:53:12.1167904Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url
qa-check	Complete job	﻿2026-04-04T23:53:12.1506139Z Cleaning up orphan processes
qa-check	Complete job	2026-04-04T23:53:12.1775415Z ##[warning]Node.js 20 actions are deprecated. The following actions are running on Node.js 20 and may not work as expected: actions/checkout@v4. Actions will be forced to run with Node.js 24 by default starting June 2nd, 2026. Node.js 20 will be removed from the runner on September 16th, 2026. Please check if updated versions of these actions are available that support Node.js 24. To opt into Node.js 24 now, set the FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true environment variable on the runner or in your workflow file. Once Node.js 24 becomes the default, you can temporarily opt out by setting ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
