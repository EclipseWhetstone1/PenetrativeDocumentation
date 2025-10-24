import React, { useState, useEffect } from 'react';

function AttackTimeline() {
  const [timelineData, setTimelineData] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch timeline data from the JSON file
    fetch('/attack_timeline.json')
      .then(response => response.json())
      .then(data => {
        setTimelineData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching timeline data:', error);
        setLoading(false);
      });
  }, []);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const closeDetails = () => {
    setSelectedNode(null);
  };

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading attack timeline...</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>Attack Timeline Visualization</h2>
      
      <div style={{ position: 'relative' }}>
        {timelineData.map((event, index) => (
          <div key={index} style={{ marginBottom: '40px', position: 'relative' }}>
            <div 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                padding: '15px',
                borderRadius: '10px',
                backgroundColor: '#f8f9fa',
                border: '2px solid transparent',
                marginLeft: '60px',
                transition: 'all 0.3s ease'
              }}
              onClick={() => handleNodeClick(event)}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#e9ecef';
                e.target.style.borderColor = '#007bff';
                e.target.style.transform = 'translateX(5px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#f8f9fa';
                e.target.style.borderColor = 'transparent';
                e.target.style.transform = 'translateX(0)';
              }}
            >
              <div style={{
                position: 'absolute',
                left: '-50px',
                width: '40px',
                height: '40px',
                background: 'linear-gradient(135deg, #007bff, #0056b3)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                boxShadow: '0 2px 8px rgba(0, 123, 255, 0.3)',
                zIndex: 2
              }}>
                <span>{index + 1}</span>
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '1.2rem', fontWeight: '600' }}>
                  {event.title}
                </h3>
                <p style={{ margin: '0', color: '#666', fontSize: '0.9rem' }}>
                  {formatTimestamp(event.timestamp)}
                </p>
              </div>
            </div>
            
            {index < timelineData.length - 1 && (
              <div style={{
                position: 'absolute',
                left: '-30px',
                top: '40px',
                width: '2px',
                height: '40px',
                background: 'linear-gradient(to bottom, #007bff, #dee2e6)',
                zIndex: 1
              }}></div>
            )}
          </div>
        ))}
      </div>

      {selectedNode && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(2px)'
          }} onClick={closeDetails}></div>
          <div style={{
            position: 'relative',
            background: 'white',
            borderRadius: '12px',
            padding: '0',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
          }}>
            <div style={{
              background: 'linear-gradient(135deg, #007bff, #0056b3)',
              color: 'white',
              padding: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ margin: '0', fontSize: '1.3rem' }}>{selectedNode.title}</h3>
              <button 
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: '0',
                  width: '30px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '50%',
                  transition: 'background-color 0.2s ease'
                }}
                onClick={closeDetails}
                onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                ×
              </button>
            </div>
            <div style={{ padding: '20px' }}>
              <p style={{ margin: '0 0 15px 0', lineHeight: '1.5' }}>
                <strong>Timestamp:</strong> {formatTimestamp(selectedNode.timestamp)}
              </p>
              <p style={{ margin: '0 0 15px 0', lineHeight: '1.5' }}>
                <strong>Description:</strong>
              </p>
              <p style={{
                background: '#f8f9fa',
                padding: '15px',
                borderRadius: '8px',
                borderLeft: '4px solid #007bff',
                fontStyle: 'italic',
                marginTop: '10px'
              }}>
                {selectedNode.description}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AttackTimeline;