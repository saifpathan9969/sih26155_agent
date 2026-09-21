# Master Animation Documentation

> **Target Directories Covered:**
> 1. **SIH26155 Autonomous AI Agent & Compliance Auditor UI** (`C:\Users\saifu\Downloads\sih26155_agent\frontend`)
> 2. **School & College Management ERP Portal** (`c:\Users\saifu\OneDrive\Desktop\ERP`)
>
> **Document Purpose:** Complete, exhaustive technical catalogue of all CSS keyframes, transitions, Framer Motion springs, interactive micro-animations, loading state animations, and layout transitions across both web applications.

---

## Table of Contents
1. [Architecture Overview & Stacks](#1-architecture-overview--stacks)
2. [SIH26155 Compliance Auditor UI — Animation Suite](#2-sih26155-compliance-auditor-ui--animation-suite)
   - [2.1 Custom CSS Keyframe Animations (`styles.css`)](#21-custom-css-keyframe-animations-stylescss)
   - [2.2 Tailwind CSS Micro-Animation Engine](#22-tailwind-css-micro-animation-engine)
   - [2.3 Framer Motion Spring Physics & Orchestrations](#23-framer-motion-spring-physics--orchestrations)
   - [2.4 Component-by-Component Animation Breakdown](#24-component-by-component-animation-breakdown)
3. [School & College ERP Portal — Animation Engine](#3-school--college-erp-portal--animation-engine)
   - [3.1 Design System Animation Tokens & Timing Curves (`index.css`)](#31-design-system-animation-tokens--timing-curves-indexcss)
   - [3.2 The 17 Core Keyframe Animations (`index.css`)](#32-the-17-core-keyframe-animations-indexcss)
   - [3.3 Stagger Delay Utility System](#33-stagger-delay-utility-system)
   - [3.4 JavaScript Intersection & Motion Controllers (`app.js`)](#34-javascript-intersection--motion-controllers-appjs)
   - [3.5 Landing Page Choreography (`landing.css`)](#35-landing-page-choreography-landingcss)
   - [3.6 Layout & Navigation Transitions (`layout.css`)](#36-layout--navigation-transitions-layoutcss)
4. [Comprehensive Animation Matrix & Reference Table](#4-comprehensive-animation-matrix--reference-table)
5. [Accessibility & Reduced Motion Considerations](#5-accessibility--reduced-motion-considerations)

---

## 1. Architecture Overview & Stacks

### System 1: SIH26155 Autonomous AI Agent & Compliance Auditor UI
* **Primary Framework:** React 18 with Vite
* **Motion Library:** `framer-motion` (v11.11.17)
* **Styling & Transitions:** Tailwind CSS (v3.4.15) with custom cyber/futuristic extensions
* **Animation Philosophy:** High-tech cyber aesthetic, real-time telemetry pulses, spring-based physics, progressive terminal streaming, dynamic radar sweeping, and non-blocking layout morphs.

### System 2: School & College Management ERP Portal
* **Primary Framework:** Vanilla JavaScript (ES6+), HTML5, Vanilla CSS
* **Motion Engine:** Custom CSS Keyframes & Variable-driven transition curves
* **Interaction Engine:** `IntersectionObserver` for ScrollReveal & `performance.now()` cubic easing for numeric stat counters
* **Animation Philosophy:** Institutional elegance, smooth staggered entrances, tactile hover elevations, gold shimmer reward effects, and physics-driven spring scale bounces.

---

## 2. SIH26155 Compliance Auditor UI — Animation Suite

### 2.1 Custom CSS Keyframe Animations (`styles.css`)

Located in [`frontend/src/styles.css`](file:///C:/Users/saifu/Downloads/sih26155_agent/frontend/src/styles.css):

#### 1. Radar Sweep Animation (`@keyframes radar-sweep`)
* **Class:** `.animate-radar`
* **Timing:** `2.5s linear infinite`
* **Transform:** Rotates an angular conic gradient through a complete circle.
```css
@keyframes radar-sweep {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.animate-radar {
  animation: radar-sweep 2.5s linear infinite;
}
```
* **Usage:** Used inside `CyberLoadingOverlay.jsx` on the central cybernetic scanner to simulate autonomous network asset scanning.

#### 2. Cyber Scanline (`@keyframes scanline`)
* **Class:** `.animate-scanline`
* **Timing:** `4s linear infinite`
* **Transform:** Translates a subtle brand glow gradient vertically from `-100%` to `1000%`.
```css
@keyframes scanline {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(1000%); }
}
.animate-scanline {
  animation: scanline 4s linear infinite;
}
```
* **Usage:** Fullscreen holographic overlay effect during active audit execution.

#### 3. Shimmer Effect (`@keyframes shimmer`)
* **Class:** `.shimmer`
* **Timing:** `1.8s infinite`
* **Properties:** Cycles background gradient position from `-200% 0` to `200% 0` across a 3-stop linear gradient.
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer {
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(56,189,248,0.12) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.8s infinite;
}
```
* **Usage:** Applied to `SkeletonCard.jsx`, `BlockchainLedger.jsx`, and `DeviceViewer.jsx` while data is loading.

#### 4. Pulse Glow (`@keyframes pulse-glow`)
* **Class:** `.glow-active`
* **Timing:** `2s infinite ease-in-out`
* **Properties:** Oscillates box shadow spread and opacity between 15px (0.2 alpha) and 30px (0.5 alpha).
```css
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 15px rgba(14, 165, 233, 0.2); }
  50% { box-shadow: 0 0 30px rgba(14, 165, 233, 0.5); }
}
.glow-active {
  animation: pulse-glow 2s infinite ease-in-out;
}
```
* **Usage:** Highlights active cryptographic nodes and focused panels.

---

### 2.2 Tailwind CSS Micro-Animation Engine

The application leverages Tailwind CSS utility animations across components to convey real-time network and security telemetry:

| Class | Animation Behavior | Duration / Timing | Primary Use Cases |
|---|---|---|---|
| `animate-pulse` | Opacity oscillation between 100% and 50% | `2s cubic-bezier(0.4, 0, 0.6, 1) infinite` | Live audit status dots, backend health beacon, terminal replay indicator, status badge dots |
| `animate-ping` | Scale expansion up to 2x with simultaneous fade out | `1s cubic-bezier(0, 0, 0.2, 1) infinite` | Radar scanner target blips, hero pill beacon, live mission control dispatchers |
| `animate-spin` | Continuous 360-degree rotation | `1s linear infinite` | Verification spinners (`RefreshCw`), schema normalizers (`Cpu`), radio dispatch status |
| `animate-bounce` | Vertical bounce displacement | `1s infinite` | Critical tamper alert banners, disconnected backend warning banners |

---

### 2.3 Framer Motion Spring Physics & Orchestrations

#### 1. Layout-Aware Tab Indicator Morphing (`App.jsx`)
* **Mechanism:** Shared layout animation using Framer Motion's `layoutId="activeTabIndicator"`.
* **Physics:** Smooth spring physics (`type: 'spring', stiffness: 500, damping: 35`).
* **Effect:** When switching between navigation tabs (Auditor, Human Review, Trace, Ledger, SOHO Hub), the active blue highlight pill glides smoothly across tabs without jarring jumps.

#### 2. Page Route Transitions (`App.jsx`)
* **Mechanism:** `<AnimatePresence mode="wait">`
* **Keyframes / Variants:**
  * `initial`: `{ opacity: 0, y: 8 }`
  * `animate`: `{ opacity: 1, y: 0 }`
  * `exit`: `{ opacity: 0, y: -8 }`
  * `transition`: `{ duration: 0.18, ease: 'easeOut' }`
* **Effect:** Snappy micro-transitions between views preventing visual popping.

#### 3. Modal Dialog Spring Entrances (`AuthModal.jsx`, `CyberLoadingOverlay.jsx`, `HumanReviewModal.jsx`, `ConfigManagerModal.jsx`, `ProfileModal.jsx`)
* **Backdrop:** `initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}`
* **Modal Card Physics:**
  * `initial={{ scale: 0.95, y: 15 }}`
  * `animate={{ scale: 1, y: 0 }}`
  * `exit={{ scale: 0.95, y: 15 }}`
  * `transition={{ type: 'spring', stiffness: 350, damping: 25 }}`
* **Effect:** Natural physical pop-in feeling with slight deceleration bounce.

---

### 2.4 Component-by-Component Animation Breakdown

#### `CyberLoadingOverlay.jsx`
* **Backdrop Fade:** Smooth fade in/out via `AnimatePresence`.
* **Radar Sweep:** `.animate-radar` rotating a 50% angular conic slice at 2.5s per revolution.
* **Radar Blinking Nodes:**
  * Emerald radar blip: `animate-ping` (top-4, left-6).
  * Cyan radar blip: `animate-ping` (bottom-6, right-8).
  * Purple core: `animate-pulse` (top-8, right-6).
* **Center Core Pulse:** `StepIcon` with `animate-pulse` inside glowing cyan badge.
* **Progress Bar Fill:** `motion.div style={{ width: `${progress}%` }} transition={{ duration: 0.1 }}` providing real-time smooth progress tracking across 6 autonomous pipeline stages.

#### `StatusFlipCard.jsx`
* **Card Entrance:**
  * `initial={{ opacity: 0, y: 12 }}`
  * `animate={{ opacity: 1, y: 0 }}`
  * `exit={{ opacity: 0, y: -12 }}`
* **Looping Transition Indicator Arrow:**
  * `motion.div animate={{ x: [0, 4, 0] }} transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}`
  * Subtle 4px horizontal nudge directing attention from the **BEFORE** status to the **AFTER** status.
* **Badge Transition:** `<AnimatePresence mode="wait">` wrapping the `<StatusBadge />` to smoothly morph status changes when human overrides are confirmed.

#### `StatusBadge.jsx`
* **State Change Pop-in:**
  * `motion.span key={normalized} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 450, damping: 25 }}`
* **Telemetry Dot:** Color-coded `animate-pulse` dot (emerald for PASS, rose for FAIL, amber for REVIEW).

#### `LandingPage.jsx`
* **Staggered Hero Cascade:**
  * Container: `containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.15 } } }`
  * Items: `itemVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } } }`
* **Badge Pop-in:** `initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}` with `animate-ping` cyan beacon dot.
* **Interactive Call To Action Button:**
  * `whileHover={{ scale: 1.04, boxShadow: '0 0 35px rgba(14, 165, 233, 0.45)' }}`
  * `whileTap={{ scale: 0.97 }}`
  * Creates high-engagement tactile feedback with cyan glow expansion.

#### `MissionTraceLog.jsx`
* **Live Event Stream-in:**
  * Lines appear incrementally at 70ms intervals mimicking real-time execution.
  * Line entrance: `motion.div key={idx} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.15 }}`.
* **Blinking Terminal Cursor:**
  * `motion.span animate={{ opacity: [1, 0, 1] }} transition={{ repeat: Infinity, duration: 0.8 }} className="inline-block w-2 h-4 bg-brand-400"`
* **Replay Indicator:** Pulsing badge (`animate-pulse`) during terminal playback.

#### `BlockchainLedger.jsx`
* **Verification Banner Expand:**
  * `motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}`
* **Staggered Block List:**
  * Blocks emerge sequentially: `transition={{ delay: index * 0.05 }}` with `initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}`.
* **Loading Indicators:** `animate-spin` on `RefreshCw` and `.shimmer` gradient bars.

#### `AuditReportView.jsx` & `ReportTamperView.jsx`
* **Tamper Hero Banner:**
  * `motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}`
* **Tamper Alarm:**
  * `AlertOctagon` icon with `animate-bounce` when cryptographic hash mismatch is detected.

#### `HomeSecurityHub.jsx`
* **Automatic Layout Reflow:**
  * `motion.div layout` on router security check cards, ensuring sibling cards transition smoothly when a checklist item expands to reveal fix steps.

---

## 3. School & College ERP Portal — Animation Engine

### 3.1 Design System Animation Tokens & Timing Curves (`index.css`)

Located in [`css/index.css`](file:///c:/Users/saifu/OneDrive/Desktop/ERP/css/index.css):

```css
:root {
  /* Animation Speeds & Standard Curves */
  --transition-fast:   150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base:   250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-smooth: 350ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow:   500ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

### 3.2 The 17 Core Keyframe Animations (`index.css`)

The ERP portal defines a complete modular animation library:

#### 1. `enterAnimation`
* **Class:** `.animate-enter`
* **Formula:** `from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); }`
* **Usage:** Modal and popup entrance.

#### 2. `fadeIn`
* **Class:** `.animate-fade-in`
* **Formula:** `from { opacity: 0; } to { opacity: 1; }`
* **Usage:** Dropdown menus, tooltips, tab content switches.

#### 3. `fadeInUp`
* **Class:** `.animate-fade-in-up`
* **Formula:** `from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); }`
* **Usage:** Page content, dashboard stat cards, student table records.

#### 4. `fadeInDown`
* **Class:** `.animate-fade-in-down`
* **Formula:** `from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); }`
* **Usage:** Top banner announcements, hero badges.

#### 5. `fadeOut`
* **Formula:** `from { opacity: 1; transform: translateY(0); } to { opacity: 0; transform: translateY(-10px); }`
* **Usage:** Toast dismissals, modal closures.

#### 6. `slideInLeft`
* **Class:** `.animate-slide-left`
* **Formula:** `from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); }`
* **Usage:** Sidebar drawer entrance, left-anchored drawer drawers.

#### 7. `slideInRight`
* **Class:** `.animate-slide-right`
* **Formula:** `from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); }`
* **Usage:** Toast notifications (`.toast`), right-hand action sheets.

#### 8. `scaleIn`
* **Class:** `.animate-scale-in`
* **Formula:** `from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); }`
* **Usage:** Dialogs, confirmation alerts.

#### 9. `scaleInBounce`
* **Class:** `.animate-scale-bounce`
* **Formula:**
  ```css
  0%   { opacity: 0; transform: scale(0) translateY(-100px); }
  60%  { opacity: 1; transform: scale(1.1) translateY(0); }
  80%  { transform: scale(0.95); }
  100% { transform: scale(1); }
  ```
* **Usage:** Hero badge logo in `landing.html`, success checkmarks in certificate issuing.

#### 10. `scrollReveal`
* **Class:** `.animate-scroll-reveal`
* **Formula:** `from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); }`
* **Usage:** Scroll-triggered element discovery.

#### 11. `pulse`
* **Class:** `.animate-pulse`
* **Formula:** `0%, 100% { opacity: 1; } 50% { opacity: 0.5; }` (2s ease-in-out infinite)
* **Usage:** Topbar notification indicators, live attendance status dots.

#### 12. `shimmer`
* **Formula:** `0% { background-position: -200% 0; } 100% { background-position: 200% 0; }`
* **Usage:** Skeleton placeholders for reports and marks tables.

#### 13. `countUp`
* **Formula:** `from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); }`
* **Usage:** Numeric KPI stats on initial render.

#### 14. `spin`
* **Class:** `.animate-spin`
* **Formula:** `to { transform: rotate(360deg); }` (1s linear infinite)
* **Usage:** Form submission spinners, CSV export loading states.

#### 15. `ripple`
* **Formula:** `0% { transform: scale(0); opacity: 0.4; } 100% { transform: scale(4); opacity: 0; }`
* **Usage:** Material-style click ripples on primary action buttons.

#### 16. `float`
* **Class:** `.animate-float`
* **Formula:** `0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); }` (3s ease-in-out infinite)
* **Usage:** Hero floating decorative badges, institutional seal graphics.

#### 17. `goldShimmer`
* **Formula:** `0% { background-position: -200% center; } 100% { background-position: 200% center; }` (3s linear infinite)
* **Usage:** Premium gold headers (`.gold-text`), certificate honor titles.

---

### 3.3 Stagger Delay Utility System

Predefined staggered delay classes allowing child items (table rows, card grids) to enter with cascading fluidity:

```css
.stagger-1  { animation-delay: 50ms; }
.stagger-2  { animation-delay: 100ms; }
.stagger-3  { animation-delay: 150ms; }
.stagger-4  { animation-delay: 200ms; }
.stagger-5  { animation-delay: 250ms; }
.stagger-6  { animation-delay: 300ms; }
.stagger-7  { animation-delay: 350ms; }
.stagger-8  { animation-delay: 400ms; }
.stagger-9  { animation-delay: 450ms; }
.stagger-10 { animation-delay: 500ms; }
```

---

### 3.4 JavaScript Intersection & Motion Controllers (`app.js`)

Located in [`js/app.js`](file:///c:/Users/saifu/OneDrive/Desktop/ERP/js/app.js):

#### 1. Scroll Reveal Engine (`initScrollReveal`)
Utilizes a native `IntersectionObserver` configured with `threshold: 0.1` and `rootMargin: '0px 0px -50px 0px'`. Elements with the `.reveal` class trigger with smooth transitions:
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, index) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
```

#### 2. Ease-Out Numeric Counter Engine (`animateCountUp`)
Runs a high-performance 60fps counter animation using `requestAnimationFrame` and a cubic ease-out calculation (`1 - Math.pow(1 - progress, 3)`):
```javascript
function animateCountUp(element, target, duration = 2000) {
  const start = 0;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (target - start) * easeOut);
    element.textContent = current.toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
```

#### 3. Staggered Grid Animator (`staggerAnimate`)
Applies progressive delays across selector groups:
```javascript
function staggerAnimate(selector, animationClass = 'animate-fade-in-up', delay = 80) {
  const elements = document.querySelectorAll(selector);
  elements.forEach((el, index) => {
    el.style.opacity = '0';
    setTimeout(() => {
      el.classList.add(animationClass);
      el.style.opacity = '';
    }, index * delay);
  });
}
```

#### 4. Toast Notification Queue
* Appends toast elements that slide in from the right:
  * Entrance: `slideInRight var(--transition-smooth) ease-out`
  * Exit: `fadeOut 0.3s ease-out` upon timeout (default 3000ms).

---

### 3.5 Landing Page Choreography (`landing.css`)

Located in [`css/landing.css`](file:///c:/Users/saifu/OneDrive/Desktop/ERP/css/landing.css):

* **Hero Background Glowing Orbs:**
  * `.hero::before`: `animation: float 6s ease-in-out infinite`
  * `.hero::after`: `animation: float 8s ease-in-out infinite reverse`
* **Hero Logo Entrance:**
  * `.hero-logo`: `animation: scaleInBounce 1s ease-out`
* **Hero Header Elements Sequence:**
  * `.hero-badge`: `fadeInDown 0.6s ease-out 0.3s both`
  * `.hero-title`: `fadeInUp 0.6s ease-out 0.5s both`
  * `.hero-title .gold-text`: `goldShimmer 3s linear infinite`
  * `.hero-subtitle`: `fadeInUp 0.6s ease-out 0.7s both`
  * `.hero-actions`: `fadeInUp 0.6s ease-out 0.9s both`
  * `.scroll-indicator`: `fadeIn 1s ease-out 1.5s both`
* **Interactive Hover Dynamics:**
  * `.feature-card:hover`: `transform: translateY(-6px); box-shadow: var(--shadow-lg)`
  * `.feature-card:hover .feature-icon`: `transform: scale(1.1)`
  * `.landing-nav-cta:hover`: `transform: translateY(-1px); box-shadow: var(--shadow-glow-gold)`

---

### 3.6 Layout & Navigation Transitions (`layout.css`)

Located in [`css/layout.css`](file:///c:/Users/saifu/OneDrive/Desktop/ERP/css/layout.css):

* **Sidebar Collapse / Expand:**
  * `transition: width var(--transition-smooth), transform var(--transition-smooth)` (transitions between 270px and 72px).
* **Main Content Area Shift:**
  * `transition: margin-left var(--transition-smooth)`
* **Notification Pulse:**
  * `.topbar-notification-badge`: `animation: pulse 2s ease-in-out infinite`
* **Dropdown Menus:**
  * `.topbar-dropdown`: `animation: fadeIn var(--transition-base) ease-out`
* **Mobile Drawer:**
  * Mobile sidebar drawer translates from `translateX(-100%)` to `translateX(0)` with smooth backdrop fade.

---

## 4. Comprehensive Animation Matrix & Reference Table

| Animation Identifier | Technology / Source | Duration & Easing | Trigger / Occurrence | Description |
|---|---|---|---|---|
| **Radar Sweep** | CSS Keyframe (`styles.css`) | `2.5s linear infinite` | Loading overlay mounted | 360° continuous rotation of scanner gradient beam |
| **Cyber Scanline** | CSS Keyframe (`styles.css`) | `4s linear infinite` | Loading overlay mounted | Holographic vertical scanline sweep |
| **Shimmer Bar** | CSS Keyframe (`styles.css` / `index.css`) | `1.8s - 2s infinite` | Skeleton loading | Shimmer gradient cycling across placeholder elements |
| **Pulse Glow** | CSS Keyframe (`styles.css`) | `2s infinite ease-in-out` | Active cryptographic components | Cyan box-shadow glow oscillation (15px to 30px) |
| **Status Beacon Ping** | Tailwind (`animate-ping`) | `1s cubic-bezier(0, 0, 0.2, 1)` | Radar blips, active hero badges | Radar blips ping outward and fade to zero opacity |
| **Status Beacon Pulse** | Tailwind (`animate-pulse`) | `2s cubic-bezier(0.4, 0, 0.6, 1)` | StatusBadge, live indicators | Subtle opacity pulse between 50% and 100% |
| **Tamper Alarm Bounce** | Tailwind (`animate-bounce`) | `1s infinite` | Tamper detection alert | High-visibility vertical bounce on tamper warning icon |
| **Processing Spinner** | Tailwind (`animate-spin`) | `1s linear infinite` | Refresh / Ingestion buttons | Smooth 360° rotation on verification/reload icons |
| **Tab Indicator Spring** | Framer Motion (`App.jsx`) | Spring (`stiffness: 500, damping: 35`) | Tab navigation switch | Physical sliding pill morphing under active tab |
| **Page View Transition** | Framer Motion (`App.jsx`) | `0.18s easeOut` | Tab/Page switch | Subtle `y: 8px` cross-fade on main content container |
| **Modal Spring Pop** | Framer Motion (`*Modal.jsx`) | Spring (`stiffness: 350, damping: 25`) | Modal opening | Physics-based scale (0.95 to 1) and slide (15px to 0) |
| **Status Flip Card Nudge** | Framer Motion (`StatusFlipCard.jsx`) | `1.5s easeInOut infinite` | Card mounted | Continuous horizontal nudge `x: [0, 4, 0]` on transition arrow |
| **Status Badge Pop-in** | Framer Motion (`StatusBadge.jsx`) | Spring (`stiffness: 450, damping: 25`) | Status state update | Spring scale (0.9 to 1) upon verdict computation |
| **Hero Cascade Entrance** | Framer Motion (`LandingPage.jsx`) | Stagger (`0.1s`), Easing `[0.22, 1, 0.36, 1]` | Landing page load | Sequential reveal of badge, headline, subtitle, CTAs |
| **CTA Hover & Tap** | Framer Motion (`LandingPage.jsx`) | Micro-interaction | User hover / tap | Scales to 1.04 with 35px glow on hover; scales to 0.97 on click |
| **Terminal Stream-in** | Framer Motion (`MissionTraceLog.jsx`) | Progressive (70ms cadence) | Mission start | Terminal events slide in from `-6px` horizontally |
| **Terminal Blinking Cursor** | Framer Motion (`MissionTraceLog.jsx`) | `0.8s infinite` | During active trace | Blinking block cursor toggling opacity `[1, 0, 1]` |
| **Float (Orbs & Badges)** | CSS Keyframe (`index.css` / `landing.css`) | `3s - 8s ease-in-out infinite` | Persistent ambient | Soft floating vertical hover displacement (-10px) |
| **Gold Shimmer** | CSS Keyframe (`index.css` / `landing.css`) | `3s linear infinite` | Headers & certificates | Metallic gold gradient shifting across typography |
| **Scale In Bounce** | CSS Keyframe (`index.css`) | `600ms - 1000ms spring` | Hero logo / Badge reward | Overshooting scale entrance from 0 to 1.1 to 1.0 |
| **Scroll Reveal** | CSS + JS (`app.js` / `index.css`) | `0.6s ease-out` | Viewport entry (IntersectionObserver) | Elements translate up 40px and fade to 100% opacity |
| **Numeric Count-up** | JS `requestAnimationFrame` (`app.js`) | `2000ms cubic ease-out` | KPI card entry (IntersectionObserver) | Numerical stats count up smoothly from 0 to target value |
| **Toast Slide-in** | CSS Keyframe (`index.css`) | `350ms ease-out` | Alert dispatch | Toast notification translates in from right (`+30px`) |
| **Button Click Ripple** | CSS Keyframe (`index.css`) | `600ms ease-out` | Button click event | Expanding circular wave scaling from 0 to 4x with fade |

---

## 5. Accessibility & Reduced Motion Considerations

Both web systems are structured with standard CSS transition variables and modular motion hooks. For optimal compliance with WCAG 2.1 Level AAA (Section 2.3.3: Animation from Interactions), the following recommendations apply:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

In Framer Motion components, disabling animations for users with reduced motion preferences can be handled via:
```javascript
import { useReducedMotion } from 'framer-motion';
const shouldReduceMotion = useReducedMotion();
// initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
```

---
*Documentation compiled automatically on 2026-09-08.*
