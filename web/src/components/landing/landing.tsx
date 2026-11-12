"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRef, useState } from "react";
import {
  motion,
  useInView,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
  useTransform,
  type MotionValue,
} from "motion/react";
import {
  ArrowDown,
  ArrowUpRight,
  Check,
  CheckCheck,
  Heart,
  Leaf,
  MessageCircle,
  Mouse,
  Pause,
  Play,
  ShieldCheck,
  Sparkles,
  Store,
  Users,
} from "lucide-react";
import { Brand } from "@/components/brand";
import { ShopFallback } from "./shop-fallback";
import evidence from "@/data/evidence.json";
import { cn } from "@/lib/utils";

const ShopScene = dynamic(() => import("./shop-scene"), {
  ssr: false,
  loading: () => <ShopFallback />,
});
const model = evidence.transferable;
const chapters = [
  {
    label: "01 / REMEMBER THE PERSON",
    title: "A conversation. Never just a customer.",
    text: "The oat milk they love. The birthday they’re planning. Nudgely turns the little things people tell your shop into a reason to reconnect.",
    note: "A little memory goes a long way.",
    bubble: "Can tell me when oat milk is back?",
    tag: "Remembers: oat milk restock",
  },
  {
    label: "02 / MAKE THE NUDGE COUNT",
    title: "Right person. Thoughtful timing.",
    text: "Some people will visit anyway. Some need a little nudge. Find the people your message could make a difference to, then make it personal.",
    note: "A thoughtful draft. Your final say.",
    bubble: "Hi Aisha, your oat milk is back. Save you a carton?",
    tag: "A draft for the shop owner to review",
  },
  {
    label: "03 / LEARN WHAT WORKS",
    title: "More than a reply. A reason to return.",
    text: "Keep a small group unmessaged and compare what happens next. Learn whether your nudge brought people back, and make the next one a little better.",
    note: "A small experiment. An honest answer.",
    bubble: "Did the nudge make a difference?",
    tag: "Compare with a no-message control group",
  },
];

function Scene({
  progress,
  hero = false,
  still,
}: {
  progress: MotionValue<number>;
  hero?: boolean;
  still: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const visible = useInView(ref, { once: true, margin: "200px" });
  return (
    <div
      ref={ref}
      className="n-shop-canvas"
      data-testid={hero ? "hero-scene" : "story-scene"}
    >
      {visible && !still ? (
        <ShopScene
          progress={progress}
          hero={hero}
          fallback={<ShopFallback />}
        />
      ) : (
        <ShopFallback />
      )}
    </div>
  );
}

function Chapter({
  index,
  progress,
  still,
}: {
  index: number;
  progress: MotionValue<number>;
  still: boolean;
}) {
  const start = index / 3;
  const opacity = useTransform(
    progress,
    [
      start,
      start + 0.02,
      start + 0.28,
      Math.min(1, start + 0.32),
    ],
    [index === 0 ? 1 : 0, 1, 1, index === 2 ? 1 : 0],
  );
  const y = useTransform(
    progress,
    [start, start + 0.12, start + 0.3],
    [20, 0, -20],
  );
  const chapter = chapters[index];
  return (
    <motion.article
      className="n-chapter"
      style={still ? undefined : { opacity, y }}
    >
      <p className="n-kicker">{chapter.label}</p>
      <h2>{chapter.title}</h2>
      <p className="n-chapter-description">{chapter.text}</p>
      <div className="n-story-message">
        <MessageCircle size={18} />
        <p>{chapter.bubble}</p>
        <CheckCheck size={15} />
      </div>
      <p className="n-message-label">{chapter.tag}</p>
      <div className="n-chapter-note">
        <span>
          <Check size={13} />
        </span>
        {chapter.note}
      </div>
    </motion.article>
  );
}

function Story({ still }: { still: boolean }) {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  });
  const [active, setActive] = useState(0),
    [started, setStarted] = useState(false);
  useMotionValueEvent(scrollYProgress, "change", (v) => {
    setActive(Math.min(2, Math.floor(v * 3)));
    setStarted(v > 0.04);
  });
  function goTo(i: number) {
    const el = ref.current;
    if (!el) return;
    const top = el.getBoundingClientRect().top + window.scrollY;
    const travel = el.offsetHeight - window.innerHeight;
    window.scrollTo({ top: top + travel * ((i + 0.45) / 3), behavior: "smooth" });
  }
  return (
    <section
      ref={ref}
      id="how"
      className={cn("n-story", still && "n-story-static")}
      aria-label="The Nudgely story"
    >
      <div className="n-story-stage">
        <div className="n-story-heading">
          <span className="n-tiny-dot" /> ONE LITTLE SHOP. A LITTLE MORE
          POSSIBILITY.
        </div>
        <div className="n-story-world">
          <div className="n-story-disc" />
          <Scene progress={scrollYProgress} still={still} />
          <span className="n-world-caption">
            Kampung Fresh · our fictional neighbourhood shop
          </span>
        </div>
        <div className="n-chapters">
          {chapters.map((_, i) => (
            <Chapter
              key={i}
              index={i}
              progress={scrollYProgress}
              still={still}
            />
          ))}
        </div>
        {!still && (
          <div className="n-story-rail" aria-label="Story chapters">
            <div className="n-rail-track">
              <motion.span style={{ scaleY: scrollYProgress }} />
            </div>
            {["Remember", "Nudge", "Learn"].map((label, i) => (
              <button
                key={label}
                className={cn("n-rail-dot", i <= active && "is-on")}
                style={{ top: `${(i / 2) * 100}%` }}
                onClick={() => goTo(i)}
                aria-label={`Go to chapter ${i + 1}: ${label}`}
                aria-current={i === active ? "step" : undefined}
                title={`${i + 1}. ${label}`}
              />
            ))}
            <span className={cn("n-rail-hint", started && "is-hidden")}>
              <Mouse size={15} /> Scroll
            </span>
          </div>
        )}
        <div className="n-story-progress">
          <div>
            <motion.span style={{ scaleX: still ? 1 : scrollYProgress }} />
          </div>
          <p>
            <span>01 Remember</span>
            <span>02 Nudge</span>
            <span>03 Learn</span>
          </p>
        </div>
      </div>
    </section>
  );
}

function Underline() {
  return (
    <svg viewBox="0 0 500 22" aria-hidden="true">
      <path
        d="M4 15C98 1 298 3 492 12M54 20C202 9 329 10 444 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Landing() {
  const reducedMotion = useReducedMotion();
  const [paused, setPaused] = useState(false);
  const still = !!reducedMotion || paused;
  const heroRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const noteY = useTransform(scrollYProgress, [0, 1], [0, -85]);
  const badgeY = useTransform(scrollYProgress, [0, 1], [0, -120]);
  return (
    <div className="nudgely-landing" id="top">
      <header className="n-nav">
        <Brand />
        <nav aria-label="Main navigation">
          <a className="n-nav-story" href="#how">
            The little story
          </a>
          <a className="n-nav-evidence" href="#evidence">
            The evidence
          </a>
          <Link className="n-nav-cta" href="/demo">
            Explore the app <ArrowUpRight size={16} />
          </Link>
        </nav>
      </header>
      <main id="main">
        <section className="n-hero" ref={heroRef}>
          <div className="n-hero-copy">
            <p className="n-kicker">
              <span className="n-tiny-dot" /> A LITTLE MORE HUMAN. A LITTLE MORE
              LOCAL.
            </p>
            <h1>
              A little nudge.
              <br />A{" "}
              <span>
                lasting connection.
                <Underline />
              </span>
            </h1>
            <p className="n-hero-description">
              Your regulars are more than a name on a list.
              <br className="n-desktop-break" /> Remember the little things.
              Give them a reason to come back.
            </p>
            <div className="n-actions">
              <Link className="n-button n-button-green" href="/demo">
                Try a conversation <ArrowUpRight size={17} />
              </Link>
              <a className="n-button n-button-outline" href="#how">
                Watch the story <ArrowDown size={16} />
              </a>
            </div>
          </div>
          <div className="n-hero-world">
            <div className="n-hero-disc" />
            <Scene progress={scrollYProgress} hero still={still} />
            <motion.div
              className="n-floating-note"
              style={still ? undefined : { y: noteY }}
            >
              <div className="n-note-top">
                <span className="n-avatar">A</span>
                <div>
                  <strong>Aisha</strong>
                  <span>A familiar face</span>
                </div>
                <Heart size={17} />
              </div>
              <p>
                “Let me know when
                <br />
                the oat milk is back?”
              </p>
              <span className="n-note-tag">
                <Sparkles size={13} /> A little thing, remembered.
              </span>
            </motion.div>
            <motion.div
              className="n-floating-success"
              style={still ? undefined : { y: badgeY }}
            >
              <span>
                <Check size={17} />
              </span>
              <div>
                <strong>One thoughtful follow-up.</strong>
                <p>A reason to pop by again.</p>
              </div>
            </motion.div>
            <div className="n-round-badge">
              <Leaf size={28} strokeWidth={1.5} />
              <span>
                SMALL SHOP.
                <br />
                BIG HEART.
              </span>
            </div>
            <svg
              className="n-hand-arrow"
              viewBox="0 0 120 100"
              aria-hidden="true"
            >
              <path
                d="M8 12C83 2 24 82 91 76M76 61L95 77 77 87"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="n-shop-caption">
              Meet Kampung Fresh. Our story starts here.
            </span>
          </div>
          <div className="n-hero-bottom">
            <span>
              <Store size={15} /> Made for shops that care.
            </span>
            <a href="#how">
              A little scroll goes a long way <ArrowDown size={14} />
            </a>
            <button
              onClick={() => setPaused(!paused)}
              aria-pressed={still}
              disabled={!!reducedMotion}
            >
              {still ? <Play size={13} /> : <Pause size={13} />}
              {reducedMotion
                ? "Reduced motion on"
                : paused
                  ? "Enable 3D motion"
                  : "Pause 3D motion"}
            </button>
          </div>
        </section>
        <div className="n-intro">
          <p>Big on the little things.</p>
          <span>
            THEIR WORDS <ArrowUpRight size={16} /> YOUR NEXT NUDGE{" "}
            <ArrowUpRight size={16} /> A LASTING CONNECTION
          </span>
        </div>
        <Story still={still} />
        <section className="n-details n-container">
          <div className="n-section-heading">
            <p className="n-kicker">THOUGHTFUL BY DESIGN</p>
            <h2>
              Less broadcasting.
              <br />
              <span>More understanding.</span>
            </h2>
            <p>
              Because “we haven’t seen you in a while” means more
              <br className="n-desktop-break" /> when you remember why they came
              in the first place.
            </p>
          </div>
          <div className="n-bento">
            <article className="n-feature n-feature-memory">
              <span className="n-feature-icon">
                <MessageCircle size={23} />
              </span>
              <h3>
                Every conversation
                <br />
                has a little clue.
              </h3>
              <p>
                Keep useful details from your chats, with the customer’s own
                words behind them.
              </p>
              <div className="n-memory-example">
                <div className="n-chat-date">
                  A LITTLE CHAT AT KAMPUNG FRESH
                </div>
                <div className="n-chat-example">
                  Planning my daughter’s birthday.
                  <br />
                  Do you have snack bundles?
                  <span>
                    10:42 <CheckCheck size={13} />
                  </span>
                </div>
                <div className="n-memory-tag">
                  <Sparkles size={15} />
                  <div>
                    <strong>Something to remember</strong>
                    <p>Birthday planning · snack bundles</p>
                  </div>
                  <Check size={16} />
                </div>
              </div>
              <span className="n-example-caption">
                Illustrative conversation
              </span>
            </article>
            <article className="n-feature n-feature-audience">
              <span className="n-feature-icon">
                <Users size={23} />
              </span>
              <h3>
                A smaller audience.
                <br />A more meaningful message.
              </h3>
              <p>
                Focus on people whose next visit your nudge could influence,
                instead of messaging everyone.
              </p>
              <div className="n-people" aria-hidden="true">
                {Array.from({ length: 28 }, (_, i) => (
                  <span
                    key={i}
                    className={
                      [3, 8, 9, 10, 15, 16, 17, 23].includes(i)
                        ? "n-person n-person-selected"
                        : "n-person"
                    }
                  >
                    <i />
                    <b />
                  </span>
                ))}
              </div>
              <div className="n-audience-legend">
                <span />
                <p>A little nudge could help</p>
                <small>Illustrative audience</small>
              </div>
            </article>
          </div>
          <div className="n-guardrails">
            <div>
              <ShieldCheck />
              <p>
                <strong>You’re in the loop.</strong>
                <span>Review each draft before it goes out.</span>
              </p>
            </div>
            <div>
              <MessageCircle />
              <p>
                <strong>People, when it matters.</strong>
                <span>Ask for HUMAN to request a person.</span>
              </p>
            </div>
            <div>
              <Heart />
              <p>
                <strong>Their choice, always.</strong>
                <span>STOP opts out. START opts back in.</span>
              </p>
            </div>
          </div>
        </section>
        <section id="evidence" className="n-evidence">
          <div className="n-container n-evidence-grid">
            <div className="n-evidence-copy">
              <p className="n-kicker">A LITTLE SCIENCE BEHIND THE NUDGE</p>
              <h2>
                A nudge should
                <br />
                make a difference.
              </h2>
              <p>
                In a historical grocery experiment, our model’s top 30% captured
                about 57% of the estimated incremental effect. Random targeting
                would capture 30% on average.
              </p>
              <a
                href="https://github.com/Morn-Thuta/nudgely/blob/main/docs/Numbers.md"
                target="_blank"
                rel="noreferrer"
              >
                See the numbers behind the story <ArrowUpRight size={17} />
              </a>
            </div>
            <div className="n-evidence-numbers">
              <div className="n-big-number">
                {Math.round(model.capture_mean * 100)}
                <span>%</span>
                <svg viewBox="0 0 330 170" aria-hidden="true">
                  <path d="M287 28C168-19-20 12 6 98C32 178 296 181 320 99C336 46 258 4 144 10" />
                </svg>
              </div>
              <p>estimated effect captured by the top 30%</p>
              <div className="n-mini-stats">
                <div>
                  <strong>
                    {(model.capture_mean / evidence.random_baseline).toFixed(1)}
                    ×
                  </strong>
                  <span>random targeting</span>
                </div>
                <div>
                  <strong>{model.seeds.length}</strong>
                  <span>random splits</span>
                </div>
                <div>
                  <strong>38–85%</strong>
                  <span>observed range</span>
                </div>
              </div>
            </div>
            <p className="n-evidence-caveat">
              Historical overseas dataset (Lenta), not a live result from
              Kampung Fresh. The range is across seven random splits, not a
              confidence interval. Small-shop outcomes still need to be measured
              locally.
            </p>
          </div>
        </section>
        <section className="n-next n-container">
          <div className="n-section-heading">
            <p className="n-kicker">YOUR TURN TO STEP INSIDE</p>
            <h2>
              From “hello” to
              <br />
              <span>“see you again.”</span>
            </h2>
          </div>
          <div className="n-steps">
            {[
              {
                icon: MessageCircle,
                title: "Read the conversations.",
                text: "See what customers asked our fictional shop about oat milk, snack bundles and parties.",
              },
              {
                icon: Sparkles,
                title: "See the little details.",
                text: "Explore how conversations become customer memories in the demo workspace.",
              },
              {
                icon: ArrowUpRight,
                title: "Try a thoughtful nudge.",
                text: "Review a draft and rehearse a campaign. Demo sends are simulated.",
              },
            ].map(({ icon: Icon, title, text }, i) => (
              <article key={title}>
                <div>
                  <span>0{i + 1}</span>
                  <Icon size={24} />
                </div>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="n-final n-container">
          <div className="n-final-copy">
            <span className="n-final-icon">
              <Store size={30} strokeWidth={1.5} />
            </span>
            <p className="n-kicker">THE DOOR’S OPEN</p>
            <h2>
              Come on in.
              <br />
              We’ve saved you
              <br />
              <span>a little space.</span>
            </h2>
            <p>Meet Nudgely at Kampung Fresh.</p>
            <Link className="n-button n-button-green" href="/demo">
              Step inside the app <ArrowUpRight size={17} />
            </Link>
            <p className="n-team-note">
              Made with care by Thuta, Dythan, Jack & Shareef.
              <br />
              Kampung Fresh and its customers are fictional.
            </p>
          </div>
        </section>
      </main>
      <footer className="n-footer n-container">
        <div>
          <Brand />
          <p>A little more human. A little more local.</p>
        </div>
        <nav aria-label="Footer navigation">
          <Link href="/login">
            Team sign in <ArrowUpRight size={14} />
          </Link>
          <a href="#top">Back to the little shop ↑</a>
        </nav>
      </footer>
    </div>
  );
}
