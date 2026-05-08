import React from 'react';

const ArchitectureDiagram = () => {
  return (
    <div className="w-full flex justify-center items-center p-8 bg-[#0a0a0f] rounded-xl border border-slate-800 shadow-2xl">
      <div className="w-full max-w-7xl aspect-[16/9] relative">
        <img 
          src="/docs/architecture.svg" 
          alt="GraphMind Architecture Diagram" 
          className="w-full h-full object-contain drop-shadow-2xl"
        />
      </div>
    </div>
  );
};

export default ArchitectureDiagram;