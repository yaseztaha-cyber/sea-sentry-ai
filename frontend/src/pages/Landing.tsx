import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const UNSPLASH_HERO = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80';
const UNSPLASH_COAST = 'https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1600&q=80';

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in'); });
    }, { threshold: 0.12 });
    els.forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);
}

export default function Landing() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  useReveal();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const navTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMobileOpen(false);
  };

  return (
    <div>
      {/* NAV */}
      <nav className={`nav ${scrolled ? 'scrolled' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
            <circle cx="13" cy="13" r="12" stroke="currentColor" strokeWidth="1" />
            <path d="M4 13 Q13 6 22 13 Q13 20 4 13Z" stroke="currentColor" strokeWidth="1" fill="none" />
            <circle cx="13" cy="13" r="2" fill="currentColor" />
          </svg>
          <span className="serif" style={{ fontSize: 18 }}>Sea Sentry</span>
        </div>
        <div className="nav-links">
          <a href="#home" onClick={(e)=>{e.preventDefault();navTo('home');}}>Home</a>
          <a href="#technology" onClick={(e)=>{e.preventDefault();navTo('technology');}}>Technology</a>
          <a href="#how" onClick={(e)=>{e.preventDefault();navTo('how');}}>How It Works</a>
          <a href="#mission" onClick={(e)=>{e.preventDefault();navTo('mission');}}>Our Mission</a>
          <a href="#about" onClick={(e)=>{e.preventDefault();navTo('about');}}>About Us</a>
        </div>
        <Link to="/app" className="nav-cta">Explore Platform</Link>
        <button className="mobile-menu-btn" onClick={() => setMobileOpen(!mobileOpen)}>☰</button>
      </nav>
      {mobileOpen && (
        <div style={{ position: 'fixed', top: 70, left: 0, right: 0, background: 'var(--ivory)', zIndex: 49, padding: 20, display: 'flex', flexDirection: 'column', gap: 12, borderBottom: '1px solid var(--stone)' }}>
          {['home','technology','how','mission','about'].map(id => (
            <a key={id} href={`#${id}`} onClick={(e)=>{e.preventDefault();navTo(id);}} style={{ fontSize: 16 }}>{id}</a>
          ))}
          <Link to="/app" onClick={()=>setMobileOpen(false)}>Explore Platform</Link>
        </div>
      )}

      {/* HERO */}
      <section id="home" className="hero">
        <div className="container hero-grid">
          <div>
            <div className="brand-label reveal">SEA SENTRY AI / COASTAL SAFETY INTELLIGENCE</div>
            <h1 className="serif reveal" style={{ transitionDelay: '.1s' }}>
              Every second matters.<br/>Every life deserves a watch.
            </h1>
            <p className="reveal" style={{ transitionDelay: '.25s' }}>
              Intelligent coastal monitoring that connects computer vision, continuous observation, and real-time incident awareness to support human rescue teams.
            </p>
            <div className="reveal" style={{ transitionDelay: '.4s', marginTop: 36, display: 'flex', gap: 14, flexWrap: 'wrap' }}>
              <Link to="/app" className="btn btn-primary">Explore the platform</Link>
              <a href="#technology" onClick={(e)=>{e.preventDefault();navTo('technology');}} className="btn btn-ghost">Discover the technology</a>
            </div>
          </div>
          <div className="hero-img reveal" style={{ transitionDelay: '.2s' }}>
            <img src={UNSPLASH_HERO} alt="Coastal shoreline" />
          </div>
        </div>
        <div className="wave-band">
          <svg className="wave slow" viewBox="0 0 1440 120" preserveAspectRatio="none">
            <path d="M0,60 C240,120 480,0 720,60 C960,120 1200,0 1440,60 L1440,120 L0,120 Z" />
          </svg>
          <svg className="wave mid" viewBox="0 0 1440 120" preserveAspectRatio="none">
            <path d="M0,80 C360,20 720,100 1080,40 C1260,10 1380,70 1440,50 L1440,120 L0,120 Z" />
          </svg>
          <svg className="wave fast" viewBox="0 0 1440 120" preserveAspectRatio="none">
            <path d="M0,90 C300,30 600,90 900,50 C1100,20 1300,80 1440,60 L1440,120 L0,120 Z" />
          </svg>
        </div>
      </section>

      {/* PROBLEM */}
      <section id="problem">
        <div className="container two-col">
          <div className="reveal">
            <div className="section-label">The Challenge</div>
            <h2 className="section-title">At the coast, every moment counts.</h2>
            <p style={{ marginTop: 24, fontSize: 17, lineHeight: 1.7, opacity: .8 }}>
              Coastal monitoring has visibility limitations. Human observation alone is demanding. Fixed camera systems cannot cover every area. Recognizing abnormal behavior is difficult. Emergency response benefits from earlier awareness.
            </p>
          </div>
          <div className="reveal" style={{ borderRadius: 10, overflow: 'hidden', aspectRatio: '4/3' }}>
            <img src={UNSPLASH_COAST} alt="Coastal observation" style={{ width:'100%', height:'100%', objectFit:'cover' }} />
          </div>
        </div>
      </section>

      {/* APPROACH */}
      <section id="how" className="dark-section">
        <div className="container">
          <div className="section-label" style={{ color: 'var(--sea-glass)' }}>The Approach</div>
          <h2 className="section-title" style={{ color: 'var(--ivory)' }}>From observation to action.</h2>
          <div className="five-col" style={{ marginTop: 60 }}>
            {[
              ['01','OBSERVE','Receive video from fixed cameras and compatible aerial sources.'],
              ['02','DETECT','Identify and track people through computer vision.'],
              ['03','ANALYZE','Evaluate temporal patterns and potential abnormal behavior.'],
              ['04','ALERT','Create incident records and notify the operator.'],
              ['05','RESPOND','Enable human lifeguards to review and coordinate the response.'],
            ].map(([n,t,d],i) => (
              <div key={t} className="reveal" style={{ transitionDelay: `${i*.1}s` }}>
                <div className="mono" style={{ fontSize: 12, opacity: .5, marginBottom: 12 }}>{n}</div>
                <div className="serif" style={{ fontSize: 22, marginBottom: 10 }}>{t}</div>
                <div style={{ fontSize: 13, opacity: .7, lineHeight: 1.6 }}>{d}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TECHNOLOGY */}
      <section id="technology">
        <div className="container">
          <div className="section-label">Technology</div>
          <h2 className="section-title">Intelligence built around observation.</h2>
          <div style={{ marginTop: 60, display: 'grid', gap: 80 }}>
            {[
              ['Computer Vision','Person detection, bounding boxes, tracking IDs, and movement analysis. Built on real camera frames with YOLO person detection and ByteTrack tracking.'],
              ['Spatial Activity Mapping','People-density heat maps from tracked positions over time. Activity concentration, not thermal imaging.'],
              ['Intelligent Incident Alerts','Suspicious observations, evidence capture, incident generation, real-time notifications, and human acknowledgment. Experimental behavior screening is never presented as verified drowning detection.'],
            ].map(([t,d]) => (
              <div key={t} className="reveal tech-grid">
                <h3 className="serif" style={{ fontSize: 34 }}>{t}</h3>
                <p style={{ fontSize: 17, lineHeight: 1.7, opacity: .8 }}>{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WORKFLOW */}
      <section id="workflow" className="dark-section">
        <div className="container">
          <div className="section-label" style={{ color: 'var(--sea-glass)' }}>System</div>
          <h2 className="section-title" style={{ color: 'var(--ivory)' }}>One connected observation system.</h2>
          <div className="mono reveal" style={{ marginTop: 40, fontSize: 13, lineHeight: 2, opacity: .85, letterSpacing: '.05em' }}>
            CAMERA INPUT → VIDEO ACQUISITION → PERSON DETECTION → TRACKING → BEHAVIOR ANALYSIS → INCIDENT MANAGEMENT → HUMAN RESPONSE
          </div>
        </div>
      </section>

      {/* PRODUCT EXPERIENCE */}
      <section id="product">
        <div className="container">
          <div className="section-label">Product</div>
          <h2 className="section-title">Inside the Sea Sentry platform.</h2>
          <p style={{ marginTop: 16, opacity: .7, maxWidth: 640 }}>Live camera monitoring, AI detection, tracking, activity heat map, and incident management. The application runs locally against a real webcam.</p>
          <div className="reveal" style={{ marginTop: 40 }}>
            <Link to="/app" className="btn btn-primary">Open the platform</Link>
          </div>
        </div>
      </section>

      {/* MISSION */}
      <section id="mission">
        <div className="container" style={{ maxWidth: 820 }}>
          <div className="section-label">Mission</div>
          <h2 className="section-title">Technology should protect what matters most.</h2>
          <p className="serif" style={{ marginTop: 32, fontSize: 22, lineHeight: 1.6, opacity: .85 }}>
            Sea Sentry AI is built around a simple belief: better observation can support better decisions, and better decisions can make a meaningful difference in emergency situations.
          </p>
          <p style={{ marginTop: 20, fontSize: 17, lineHeight: 1.7, opacity: .75 }}>
            By bringing computer vision, connected monitoring, and human response together, the project explores a more intelligent approach to coastal safety.
          </p>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about">
        <div className="container mission-grid">
          <div>
            <div className="section-label">About Us</div>
            <h2 className="section-title">The people and purpose behind the project.</h2>
          </div>
          <div className="reveal">
            <div className="serif" style={{ fontSize: 30 }}>Eyad Sherif Elbagoury</div>
            <div className="mono" style={{ fontSize: 12, opacity: .6, marginTop: 6, letterSpacing: '.12em', textTransform: 'uppercase' }}>Project Creator & Developer</div>
            <p style={{ marginTop: 20, fontSize: 16, lineHeight: 1.7, opacity: .8 }}>
              Sea Sentry AI is an independently developed technology project exploring how artificial intelligence, computer vision, and connected monitoring systems can support coastal safety and rescue assistance.
            </p>
            <p style={{ marginTop: 12, fontSize: 16, lineHeight: 1.7, opacity: .8 }}>
              The project focuses on creating an expandable, accessible approach to intelligent coastal observation, beginning with camera-based computer vision and developing toward connected sensors and aerial monitoring.
            </p>
          </div>
        </div>
      </section>

      {/* ROADMAP */}
      <section id="roadmap" className="dark-section">
        <div className="container">
          <div className="section-label" style={{ color: 'var(--sea-glass)' }}>Roadmap</div>
          <h2 className="section-title" style={{ color: 'var(--ivory)' }}>Development roadmap.</h2>
          <div style={{ marginTop: 48, display: 'grid', gap: 20 }}>
            {[
              ['PHASE 01 — CAMERA INTELLIGENCE','Camera connection, person detection, tracking, activity heat maps, and incident notifications. (Available today)'],
              ['PHASE 02 — CONNECTED SENSOR NETWORK','ESP32-based nodes and additional environmental sensors. (Planned)'],
              ['PHASE 03 — AERIAL OBSERVATION','Compatible and legally authorized small aerial camera platforms. (Planned)'],
              ['PHASE 04 — ADVANCED COASTAL INTELLIGENCE','Multi-camera integration, localization research, thermal experimentation, and professional rescue-support integrations. (Planned)'],
            ].map(([t,d]) => (
              <div key={t} className="reveal" style={{ padding: '20px 0', borderBottom: '1px solid rgba(255,255,255,.12)', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24 }}>
                <div className="mono" style={{ fontSize: 12, opacity: .7 }}>{t}</div>
                <div style={{ fontSize: 15, opacity: .85 }}>{d}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section id="cta" style={{ textAlign: 'center', background: 'var(--ivory)' }}>
        <div className="container">
          <h2 className="serif reveal" style={{ fontSize: 'clamp(40px,6vw,72px)' }}>Watch closer. Respond smarter.</h2>
          <p className="reveal" style={{ marginTop: 20, opacity: .7, fontSize: 17 }}>Explore the first stage of Sea Sentry AI and the technology behind intelligent coastal monitoring.</p>
          <div className="reveal" style={{ marginTop: 32 }}>
            <Link to="/app" className="btn btn-primary">Open Sea Sentry AI</Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="container footer-grid">
          <div>
            <div className="serif" style={{ fontSize: 20, marginBottom: 8 }}>Sea Sentry</div>
            <p style={{ fontSize: 13, opacity: .7, maxWidth: 360 }}>An AI-assisted coastal safety and rescue-support project.</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <a href="#technology" onClick={(e)=>{e.preventDefault();navTo('technology');}}>Technology</a>
            <a href="#about" onClick={(e)=>{e.preventDefault();navTo('about');}}>About Us</a>
            <Link to="/app">Open Platform</Link>
          </div>
          <div style={{ fontSize: 13, opacity: .6 }}>
            Project Creator: Eyad Sherif Elbagoury<br/>
            © {new Date().getFullYear()}
          </div>
        </div>
      </footer>
    </div>
  );
}
