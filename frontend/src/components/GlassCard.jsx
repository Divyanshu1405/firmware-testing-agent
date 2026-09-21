import React from 'react';
import { motion } from 'framer-motion';

/**
 * Clean minimal card — Apple-style with subtle border, no glassmorphism.
 * Variants: default, interactive, flat, elevated.
 */
export default function Card({
  children,
  variant = 'default',
  delay = 0,
  style = {},
  onClick,
  ...props
}) {
  const classMap = {
    default: 'card',
    interactive: 'card card-interactive',
    flat: 'card-flat',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}
      className={classMap[variant] || 'card'}
      style={{ cursor: onClick ? 'pointer' : 'default', ...style }}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.div>
  );
}
