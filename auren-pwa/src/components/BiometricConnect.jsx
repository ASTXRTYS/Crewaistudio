import { useState } from 'react';

const BiometricConnect = ({ userId }) => {
  const [connectedDevices, setConnectedDevices] = useState([]);

  const connectDevice = (device) => {
    if (device === 'apple') {
      // In production, this would open Terra widget
      alert('Opening Apple Health connection flow...\n\nIn production, this would open the Terra widget for seamless authorization.');
      
      // Demo: Show connected state
      setTimeout(() => {
        const newDevice = {
          id: 'apple-watch-' + Date.now(),
          type: 'apple',
          name: 'Apple Watch Series 9',
          icon: '🍎',
          lastSync: '2 minutes ago',
          status: 'Connected'
        };
        setConnectedDevices(prev => [...prev, newDevice]);
      }, 2000);
    }
  };

  return (
    <div className="biometric-connect-container">
      <div className="bc-header">
        <h1>Connect Your Devices</h1>
        <p>Sync your wearables to unlock AI-powered health insights that remember you for years, not just 30 days</p>
      </div>
      
      <div className="bc-devices-grid">
        {/* Apple Watch Card */}
        <div className="bc-device-card" onClick={() => connectDevice('apple')}>
          <div className="bc-device-icon">🍎</div>
          <div className="bc-device-name">Apple Watch</div>
          <div className="bc-device-status">Ready to connect</div>
          <button className="bc-connect-btn">Connect</button>
        </div>
        
        {/* WHOOP Card */}
        <div className="bc-device-card bc-coming-soon">
          <div className="bc-beta-badge">Coming Soon</div>
          <div className="bc-device-icon">⚡</div>
          <div className="bc-device-name">WHOOP</div>
          <div className="bc-device-status">Available soon</div>
          <button className="bc-connect-btn" disabled>Notify Me</button>
        </div>
        
        {/* Oura Card */}
        <div className="bc-device-card bc-coming-soon">
          <div className="bc-beta-badge">Coming Soon</div>
          <div className="bc-device-icon">💍</div>
          <div className="bc-device-name">Oura Ring</div>
          <div className="bc-device-status">Available soon</div>
          <button className="bc-connect-btn" disabled>Notify Me</button>
        </div>
        
        {/* Garmin Card */}
        <div className="bc-device-card bc-coming-soon">
          <div className="bc-beta-badge">Coming Soon</div>
          <div className="bc-device-icon">⌚</div>
          <div className="bc-device-name">Garmin</div>
          <div className="bc-device-status">Available soon</div>
          <button className="bc-connect-btn" disabled>Notify Me</button>
        </div>
        
        {/* MyFitnessPal Card */}
        <div className="bc-device-card bc-coming-soon">
          <div className="bc-beta-badge">Coming Soon</div>
          <div className="bc-device-icon">🍎</div>
          <div className="bc-device-name">MyFitnessPal</div>
          <div className="bc-device-status">Available soon</div>
          <button className="bc-connect-btn" disabled>Notify Me</button>
        </div>
        
        {/* Withings Card */}
        <div className="bc-device-card bc-coming-soon">
          <div className="bc-beta-badge">Coming Soon</div>
          <div className="bc-device-icon">⚖️</div>
          <div className="bc-device-name">Withings</div>
          <div className="bc-device-status">Available soon</div>
          <button className="bc-connect-btn" disabled>Notify Me</button>
        </div>
      </div>
      
      {/* Connected Devices Section */}
      {connectedDevices.length > 0 && (
        <div className="bc-connected-devices">
          <h2>Your Connected Devices</h2>
          <div className="bc-device-list">
            {connectedDevices.map((device) => (
              <div key={device.id} className="bc-device-item">
                <div className="bc-device-info">
                  <div className="bc-device-mini-icon">{device.icon}</div>
                  <div className="bc-device-details">
                    <h3>{device.name}</h3>
                    <p>Last sync: {device.lastSync}</p>
                  </div>
                </div>
                <div className="bc-sync-status">
                  <div className="bc-sync-icon"></div>
                  <span>Syncing</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BiometricConnect; 