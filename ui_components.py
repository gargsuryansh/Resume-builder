import streamlit as st

def apply_modern_styles():
    """Apply modern styles by loading the CSS file"""
    # Styles are now loaded from style.css in app.py
    pass

def page_header(title, subtitle=None):
    """Render a consistent page header with modern typography"""
    st.markdown(
        f'''
        <div class="glass-card animate-fade-in" style="margin-bottom: 2rem; border-left: 5px solid var(--primary);">
            <h1 class="header-title" style="font-size: 2.8rem !important; margin: 0;">{title}</h1>
            {f'<p class="header-subtitle" style="color: var(--text-muted); font-size: 1.1rem; margin-top: 0.5rem;">{subtitle}</p>' if subtitle else ''}
        </div>
        ''',
        unsafe_allow_html=True
    )

def hero_section(title, subtitle=None, description=None):
    """Render a premium hero section with high-end typography"""
    st.markdown(
        f'''
        <div style="text-align: center; padding: 4rem 1rem; background: radial-gradient(circle at 50% 50%, rgba(79, 209, 197, 0.1) 0%, transparent 70%); border-radius: 40px; margin-bottom: 3rem;">
            <h1 class="header-title" style="font-size: 4rem !important; margin-bottom: 1.5rem;">{title}</h1>
            {f'<div class="header-subtitle" style="font-size: 1.5rem; color: var(--primary-alt); font-weight: 600; margin-bottom: 1rem;">{subtitle}</div>' if subtitle else ''}
            {f'<p style="max-width: 800px; margin: 0 auto; color: var(--text-muted); font-size: 1.1rem; line-height: 1.6;">{description}</p>' if description else ''}
        </div>
        ''',
        unsafe_allow_html=True
    )

def feature_card(icon, title, description):
    """Render a premium feature card with glow effects"""
    st.markdown(f"""
        <div class="glass-card feature-card">
            <div class="feature-icon icon-pulse">
                <i class="{icon}"></i>
            </div>
            <h3 style="color: var(--text-main); margin-bottom: 1rem;">{title}</h3>
            <p style="color: var(--text-muted); font-size: 0.95rem;">{description}</p>
        </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, delta=None, icon=None):
    """Render a modern metric card with neon accents"""
    icon_html = f'<i class="{icon}" style="color: var(--primary); font-size: 1.5rem; margin-bottom: 0.5rem;"></i>' if icon else ''
    delta_html = f'<div style="color: var(--success); font-size: 0.8rem; margin-top: 0.5rem;">{delta}</div>' if delta else ''
    
    st.markdown(f"""
        <div class="metric-card">
            {icon_html}
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def candidate_card(name, role, skills, location, score, experience):
    """New modern card for recruiter dashboard"""
    # Format skills as tags
    skill_tags = "".join([f'<span class="skill-tag" style="background: rgba(0, 242, 254, 0.1); color: var(--primary); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; margin-right: 5px; margin-bottom: 5px; display: inline-block; border: 1px solid rgba(0, 242, 254, 0.2);">{s.strip()}</span>' for s in skills.replace("[", "").replace("]", "").replace("'", "").split(",")[:5]])
    
    st.markdown(f"""
        <div class="candidate-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h3 style="margin: 0; color: var(--text-main);">{name}</h3>
                    <p style="color: var(--primary-alt); font-size: 0.9rem; margin: 0.2rem 0;">{role}</p>
                </div>
                <div style="background: linear-gradient(135deg, var(--primary) 0%, var(--primary-alt) 100%); color: #000; padding: 5px 12px; border-radius: 12px; font-weight: 800; font-size: 1.1rem;">
                    {score}%
                </div>
            </div>
            <div style="margin: 1rem 0; color: var(--text-muted); font-size: 0.85rem;">
                <span><i class="fas fa-map-marker-alt" style="margin-right: 5px;"></i> {location or 'Not Specified'}</span>
                <span style="margin-left: 15px;"><i class="fas fa-briefcase" style="margin-right: 5px;"></i> {experience or 'N/A'}</span>
            </div>
            <div style="margin-top: 1rem;">
                {skill_tags}
            </div>
        </div>
    """, unsafe_allow_html=True)

def loading_spinner(message="Synthesizing Data..."):
    """Show a premium loading spinner with message"""
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem;">
            <div class="loading-spinner" style="width: 60px; height: 60px; border: 4px solid var(--border-glass); border-top: 4px solid var(--primary); border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <p style="margin-top: 1.5rem; color: var(--primary); font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;">{message}</p>
        </div>
        <style> @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }} </style>
    """, unsafe_allow_html=True)

def render_analytics_section(metrics=None):
    """Render the beautified analytics section with neon metric cards"""
    if not metrics:
        metrics = {'views': 0, 'downloads': 0, 'score': '0%'}
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Total Views", metrics['views'], icon="fas fa-eye")
    with col2:
        metric_card("Downloads", metrics['downloads'], icon="fas fa-download")
    with col3:
        metric_card("Avg. Profile Score", metrics['score'], icon="fas fa-chart-line")

def progress_bar(value, label=None):
    """Render a premium animated progress bar"""
    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: var(--text-main); font-weight: 600; font-size: 0.9rem;">{label}</span>
                <span style="color: var(--primary); font-weight: 700;">{value}%</span>
            </div>
            <div style="height: 8px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; border: 1px solid var(--border-glass);">
                <div style="width: {value}%; height: 100%; background: linear-gradient(90deg, var(--primary) 0%, var(--primary-alt) 100%); transition: width 1s ease-in-out;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)