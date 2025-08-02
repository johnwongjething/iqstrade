import React, { useEffect, useState } from 'react';

const WhatsAppButton = () => {
  const [show, setShow] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // Use a free IP geolocation API to detect country
    fetch('https://ipapi.co/json/')
      .then(res => res.json())
      .then(data => {
        if (data && data.country_code !== 'CN') {
          setShow(true);
        }
        setChecked(true);
      })
      .catch(() => setChecked(true));
  }, []);

  if (!checked) return null; // Don't render until check is done
  if (!show) return null;

  return (
    <a
      href="https://api.whatsapp.com/send?phone=61426254052"
      className="whatsapp-float"
      target="_blank"
      rel="noopener noreferrer"
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 1000,
        background: '#25D366',
        borderRadius: '50%',
        width: 56,
        height: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
      }}
    >
      <img src="/whatsapp-icon.png" alt="WhatsApp" style={{ width: 32, height: 32 }} />
    </a>
  );
};

export default WhatsAppButton;
