import { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useTransform } from "framer-motion";

interface SlideRulerProps {
  min: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  step?: number;
  unit?: string;
  formatLabel?: (value: number) => string;
  labelInterval?: number; // How often to show a number label (e.g., every 5 or 10 ticks)
}

export default function SlideRuler({
  min,
  max,
  value,
  onChange,
  step = 1,
  unit = "",
  formatLabel,
  labelInterval = 10,
}: SlideRulerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  // Visual configuration
  const tickSpacing = 10; // pixels per unit step
  const totalSteps = (max - min) / step;
  const totalWidth = totalSteps * tickSpacing;
  
  // Calculate initial scroll position based on value
  // We want the 'value' to be in the center of the container
  // Center of container = containerWidth / 2
  // Position of value tick = (value - min) / step * tickSpacing
  // ScrollLeft = Position of value tick - Center of container

  const handleScroll = () => {
    if (!containerRef.current || isDragging) return;
    
    const container = containerRef.current;
    const centerOffset = container.clientWidth / 2;
    const scrollLeft = container.scrollLeft;
    
    // Calculate value from scroll position
    // scrollLeft + centerOffset = current pixel position relative to start
    const currentPixel = scrollLeft + centerOffset;
    const rawStepIndex = currentPixel / tickSpacing;
    const rawValue = min + (rawStepIndex * step);
    
    const clampedValue = Math.max(min, Math.min(max, Math.round(rawValue / step) * step));
    
    if (clampedValue !== value) {
      onChange(clampedValue);
    }
  };

  // Sync scroll position when value changes externally (or on mount)
  useEffect(() => {
    if (containerRef.current && !isDragging) {
      const container = containerRef.current;
      const centerOffset = container.clientWidth / 2;
      const targetPixel = ((value - min) / step) * tickSpacing;
      const targetScroll = targetPixel - centerOffset;
      
      // Only scroll if significantly different to avoid fighting with user scroll
      if (Math.abs(container.scrollLeft - targetScroll) > 2) {
        container.scrollLeft = targetScroll;
      }
    }
  }, [value, min, step, tickSpacing, isDragging]);

  return (
    <div className="relative w-full h-24 bg-black/40 border-y border-white/10 select-none">
      {/* Center Indicator */}
      <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-primary z-20 -translate-x-1/2 shadow-[0_0_10px_var(--color-primary)] pointer-events-none"></div>
      
      {/* Scrollable Area */}
      <div 
        ref={containerRef}
        className="w-full h-full overflow-x-scroll scrollbar-hide cursor-grab active:cursor-grabbing relative flex items-center"
        onScroll={handleScroll}
        onMouseDown={() => setIsDragging(true)}
        onMouseUp={() => setIsDragging(false)}
        onMouseLeave={() => setIsDragging(false)}
        onTouchStart={() => setIsDragging(true)}
        onTouchEnd={() => setIsDragging(false)}
        style={{ scrollBehavior: isDragging ? 'auto' : 'smooth' }}
      >
        {/* Padding to allow scrolling to the very ends */}
        <div style={{ width: '50%', flexShrink: 0 }}></div>
        
        {/* Ticks Container */}
        <div 
          className="relative h-full flex items-end"
          style={{ width: `${totalWidth}px`, flexShrink: 0 }}
        >
          {Array.from({ length: totalSteps + 1 }).map((_, i) => {
            const currentValue = min + (i * step);
            const isMajor = i % labelInterval === 0;
            const isMedium = i % (labelInterval / 2) === 0;
            
            return (
              <div 
                key={i}
                className="absolute bottom-0 flex flex-col items-center justify-end group"
                style={{ left: `${i * tickSpacing}px`, transform: 'translateX(-50%)' }}
              >
                {/* Label for major ticks */}
                {isMajor && (
                  <span className="mb-2 text-xs font-bold text-muted-foreground select-none whitespace-nowrap">
                    {formatLabel ? formatLabel(currentValue) : currentValue}
                  </span>
                )}
                
                {/* Tick Mark */}
                <div 
                  className={`w-0.5 bg-white/30 transition-colors group-hover:bg-white/80 ${
                    isMajor ? 'h-8 bg-white/60' : isMedium ? 'h-5' : 'h-3'
                  }`}
                ></div>
              </div>
            );
          })}
        </div>
        
        {/* Padding to allow scrolling to the very ends */}
        <div style={{ width: '50%', flexShrink: 0 }}></div>
      </div>
      
      {/* Current Value Display Overlay (Optional, can be removed if displayed elsewhere) */}
      <div className="absolute top-2 right-4 text-xs text-primary font-mono opacity-50 pointer-events-none">
        {unit}
      </div>
    </div>
  );
}
