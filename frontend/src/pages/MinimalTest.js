import React from 'react';

const MinimalTest = () => {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🎉 Minimal Test Route Working!</h1>
      <p>If you can see this, React Router is working!</p>
      <p>Current URL: {window.location.href}</p>
    </div>
  );
};

export default MinimalTest; 