import React from 'react';

export default function Section({ step, title, description, extra, children, className = '' }) {
  return (
    <section className={`app-section ${className}`.trim()}>
      <div className="app-section-head">
        <div className="app-section-head-main">
          {step != null ? <span className="app-section-step">{step}</span> : null}
          <div className="app-section-heading">
            <h2 className="app-section-title">{title}</h2>
            {description ? <p className="app-section-desc">{description}</p> : null}
          </div>
        </div>
        {extra ? <div className="app-section-extra">{extra}</div> : null}
      </div>
      <div className="app-section-body">{children}</div>
    </section>
  );
}
