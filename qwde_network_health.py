"""
QWDE Protocol - Network Health and Topology Visualization
Real-time network map showing peers, connections, and health metrics
"""

import tkinter as tk
from tkinter import ttk, canvas
import math
import time
import threading
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """Represents a node in the network topology"""
    peer_id: str
    x: float
    y: float
    host: str = ''
    port: int = 0
    sites_count: int = 0
    is_active: bool = True
    is_self: bool = False
    connections: List[str] = None
    latency: float = 0.0
    last_seen: float = 0.0
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []


@dataclass
class NetworkConnection:
    """Represents a connection between nodes"""
    node1_id: str
    node2_id: str
    strength: float = 1.0
    latency: float = 0.0
    is_active: bool = True


class NetworkTopologyCanvas(tk.Canvas):
    """Interactive network topology visualization"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0a0a1a', highlightthickness=0, **kwargs)
        
        self.nodes: Dict[str, NetworkNode] = {}
        self.connections: List[NetworkConnection] = []
        self.selected_node: Optional[str] = None
        self.hovered_node: Optional[str] = None
        
        # Animation
        self.pulse_phase = 0
        self.animate()
        
        # Bind events
        self.bind('<Motion>', self._on_mouse_move)
        self.bind('<Leave>', self._on_mouse_leave)
        self.bind('<Button-1>', self._on_click)
        
        # Tooltip
        self.tooltip = None
    
    def clear(self):
        """Clear all nodes and connections"""
        self.nodes.clear()
        self.connections.clear()
        self.delete('all')
    
    def add_node(self, node: NetworkNode):
        """Add a node to the topology"""
        self.nodes[node.peer_id] = node
    
    def add_connection(self, connection: NetworkConnection):
        """Add a connection between nodes"""
        self.connections.append(connection)
    
    def update_node(self, peer_id: str, **kwargs):
        """Update node properties"""
        if peer_id in self.nodes:
            node = self.nodes[peer_id]
            for key, value in kwargs.items():
                if hasattr(node, key):
                    setattr(node, key, value)
    
    def remove_node(self, peer_id: str):
        """Remove a node"""
        if peer_id in self.nodes:
            del self.nodes[peer_id]
    
    def _get_node_color(self, node: NetworkNode) -> str:
        """Get node color based on status"""
        if node.is_self:
            return '#00ff88'  # Green for self
        elif node.is_active:
            return '#00aaff'  # Blue for active
        else:
            return '#ff4444'  # Red for inactive
    
    def _draw_node(self, node: NetworkNode, offset: float = 0):
        """Draw a single node"""
        cx, cy = node.x, node.y
        base_radius = 15 if node.is_self else 10
        
        # Pulse effect for active nodes
        if node.is_active:
            pulse = math.sin(self.pulse_phase + node.x * 0.1) * 3
            radius = base_radius + pulse
        else:
            radius = base_radius * 0.7
        
        color = self._get_node_color(node)
        
        # Outer glow for active nodes
        if node.is_active:
            for i in range(3, 0, -1):
                glow_radius = radius + i * 3
                glow_alpha = int(50 / i)
                glow_color = f'#{glow_alpha:02x}{glow_alpha:02x}{glow_alpha:02x}'
                self.create_oval(
                    cx - glow_radius, cy - glow_radius,
                    cx + glow_radius, cy + glow_radius,
                    fill=glow_color, outline=''
                )
        
        # Main node circle
        self.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill=color, outline='white', width=2
        )
        
        # Node label
        label = node.peer_id[-8:] if node.peer_id else 'Unknown'
        if node.is_self:
            label = 'YOU'
        
        self.create_text(
            cx, cy + radius + 12,
            text=label,
            fill='white',
            font=('Arial', 8),
            anchor='n'
        )
        
        # Sites count
        if node.sites_count > 0:
            self.create_text(
                cx, cy - radius - 8,
                text=f'📁 {node.sites_count}',
                fill='#88ff88',
                font=('Arial', 7),
                anchor='s'
            )
    
    def _draw_connection(self, conn: NetworkConnection):
        """Draw a connection between nodes"""
        if conn.node1_id not in self.nodes or conn.node2_id not in self.nodes:
            return
        
        node1 = self.nodes[conn.node1_id]
        node2 = self.nodes[conn.node2_id]
        
        # Calculate line color based on connection strength
        if conn.is_active:
            alpha = int(200 * conn.strength)
            color = f'#{alpha:02x}{alpha:02x}{alpha:02x}'
            width = 2
        else:
            color = '#333333'
            width = 1
        
        # Draw connection line
        self.create_line(
            node1.x, node1.y,
            node2.x, node2.y,
            fill=color,
            width=width,
            dash=(4, 2) if not conn.is_active else ()
        )
        
        # Draw data flow animation for active connections
        if conn.is_active and conn.strength > 0.5:
            flow_offset = (self.pulse_phase * 50) % 100 / 100
            flow_x = node1.x + (node2.x - node1.x) * flow_offset
            flow_y = node1.y + (node2.y - node1.y) * flow_offset
            
            self.create_oval(
                flow_x - 3, flow_y - 3,
                flow_x + 3, flow_y + 3,
                fill='#00ff88',
                outline=''
            )
    
    def draw(self):
        """Draw the complete topology"""
        self.delete('all')
        
        # Draw connections first (behind nodes)
        for conn in self.connections:
            self._draw_connection(conn)
        
        # Draw nodes
        for node in self.nodes.values():
            self._draw_node(node)
        
        # Draw selection indicator
        if self.selected_node and self.selected_node in self.nodes:
            node = self.nodes[self.selected_node]
            self.create_oval(
                node.x - 25, node.y - 25,
                node.x + 25, node.y + 25,
                outline='#00ff88',
                width=2,
                dash=(4, 4)
            )
    
    def animate(self):
        """Animation loop"""
        self.pulse_phase += 0.05
        self.draw()
        self.after(50, self.animate)
    
    def _on_mouse_move(self, event):
        """Handle mouse movement"""
        # Find hovered node
        self.hovered_node = None
        for peer_id, node in self.nodes.items():
            dx = event.x - node.x
            dy = event.y - node.y
            if math.sqrt(dx*dx + dy*dy) < 20:
                self.hovered_node = peer_id
                self._show_tooltip(event, node)
                break
        
        if self.hovered_node:
            self.config(cursor='hand2')
        else:
            self.config(cursor='')
            self._hide_tooltip()
    
    def _on_mouse_leave(self, event):
        """Handle mouse leave"""
        self._hide_tooltip()
    
    def _on_click(self, event):
        """Handle click"""
        self.selected_node = self.hovered_node
    
    def _show_tooltip(self, event, node: NetworkNode):
        """Show tooltip for node"""
        if self.tooltip:
            self.tooltip.destroy()
        
        x = self.winfo_rootx() + event.x + 10
        y = self.winfo_rooty() + event.y + 10
        
        info = f"""Peer: {node.peer_id}
Host: {node.host}:{node.port}
Sites: {node.sites_count}
Status: {'Active' if node.is_active else 'Offline'}
Latency: {node.latency:.0f}ms
Connections: {len(node.connections)}"""
        
        if node.is_self:
            info += "\n\n★ This is you"
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        frame = tk.Frame(self.tooltip, bg='#1a1a2e', relief=tk.SOLID, borderwidth=1)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=info,
            bg='#1a1a2e',
            fg='#00ff88',
            justify=tk.LEFT,
            padx=10,
            pady=5,
            font=('Consolas', 9)
        )
        label.pack()
    
    def _hide_tooltip(self):
        """Hide tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class NetworkHealthPanel(ttk.Frame):
    """Network health metrics panel"""
    
    def __init__(self, parent):
        super().__init__(parent, style='Dark.TFrame')
        
        self.metrics = {
            'total_peers': 0,
            'active_peers': 0,
            'total_sites': 0,
            'avg_latency': 0,
            'network_health': 100,
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0
        }
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create health metric widgets"""
        # Title
        title = ttk.Label(
            self,
            text="📊 Network Health",
            font=('Arial', 14, 'bold'),
            foreground='#00ff88'
        )
        title.pack(pady=10)
        
        # Metrics grid
        metrics_frame = ttk.Frame(self, style='Dark.TFrame')
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create metric cards
        self.metric_cards = {}
        metrics = [
            ('total_peers', 'Total Peers', '🔗'),
            ('active_peers', 'Active Peers', '✓'),
            ('total_sites', 'Total Sites', '📁'),
            ('avg_latency', 'Avg Latency', '⏱️'),
            ('network_health', 'Health', '❤️'),
            ('packets_sent', 'Sent', '📤'),
            ('packets_received', 'Received', '📥'),
            ('errors', 'Errors', '⚠️')
        ]
        
        for i, (key, label, icon) in enumerate(metrics):
            row = i // 2
            col = i % 2
            
            card = ttk.LabelFrame(
                metrics_frame,
                text=f"{icon} {label}",
                padding=10
            )
            card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            value_label = ttk.Label(
                card,
                text="0",
                font=('Arial', 24, 'bold'),
                foreground='#00aaff'
            )
            value_label.pack()
            
            self.metric_cards[key] = value_label
        
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        
        # Health bar
        health_frame = ttk.LabelFrame(self, text="Network Health Status", padding=10)
        health_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.health_bar = ttk.Progressbar(
            health_frame,
            orient=tk.HORIZONTAL,
            length=300,
            mode='determinate',
            maximum=100
        )
        self.health_bar.pack(fill=tk.X)
        
        self.health_label = ttk.Label(
            health_frame,
            text="Excellent",
            font=('Arial', 10),
            foreground='#00ff88'
        )
        self.health_label.pack(pady=5)
        
        # Status indicators
        status_frame = ttk.Frame(self, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_indicators = {
            'ddns': self._create_status_indicator(status_frame, "DDNS Server", 0),
            'p2p': self._create_status_indicator(status_frame, "P2P Network", 1),
            'sync': self._create_status_indicator(status_frame, "Sync Status", 2)
        }
    
    def _create_status_indicator(self, parent, label, index):
        """Create a status indicator"""
        frame = ttk.Frame(parent, style='Dark.TFrame')
        frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        indicator = tk.Label(
            frame,
            text="●",
            font=('Arial', 16),
            fg='#00ff88',
            bg='#1a1a2e'
        )
        indicator.pack(side=tk.LEFT)
        
        ttk.Label(
            frame,
            text=label,
            font=('Arial', 9),
            foreground='#888888',
            background='#1a1a2e'
        ).pack(side=tk.LEFT, padx=5)
        
        return indicator
    
    def update_metrics(self, metrics: dict):
        """Update health metrics"""
        self.metrics.update(metrics)
        
        # Update metric cards
        for key, value in self.metrics.items():
            if key in self.metric_cards:
                if key == 'avg_latency':
                    self.metric_cards[key].config(text=f"{value:.0f}ms")
                elif key == 'network_health':
                    self.metric_cards[key].config(text=f"{value:.0f}%")
                else:
                    self.metric_cards[key].config(text=str(value))
        
        # Update health bar
        health = self.metrics.get('network_health', 100)
        self.health_bar['value'] = health
        
        # Update health status
        if health >= 80:
            status = "Excellent"
            color = "#00ff88"
        elif health >= 60:
            status = "Good"
            color = "#88ff88"
        elif health >= 40:
            status = "Fair"
            color = "#ffaa00"
        else:
            status = "Poor"
            color = "#ff4444"
        
        self.health_label.config(text=status, foreground=color)
    
    def set_status(self, status_type: str, online: bool):
        """Set status indicator"""
        if status_type in self.status_indicators:
            color = '#00ff88' if online else '#ff4444'
            self.status_indicators[status_type].config(fg=color)


class NetworkTopologyWindow(tk.Toplevel):
    """Network topology visualization window"""
    
    def __init__(self, parent, peer=None):
        super().__init__(parent)
        self.title("🌐 Network Topology & Health")
        self.geometry("1200x800")
        self.transient(parent)
        
        self.peer = peer
        self.topology_data = {
            'nodes': {},
            'connections': []
        }
        
        self._create_ui()
        self._start_update_loop()
    
    def _create_ui(self):
        """Create UI"""
        # Main paned window
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Topology visualization
        viz_frame = ttk.LabelFrame(paned, text="Network Topology Map")
        paned.add(viz_frame, weight=3)
        
        self.topology_canvas = NetworkTopologyCanvas(viz_frame)
        self.topology_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Health metrics and controls
        control_frame = ttk.Frame(paned, style='Dark.TFrame')
        paned.add(control_frame, weight=1)
        
        # Health panel
        self.health_panel = NetworkHealthPanel(control_frame)
        self.health_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Controls
        controls_frame = ttk.LabelFrame(control_frame, text="Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            controls_frame,
            text="🔄 Refresh",
            command=self._refresh_topology
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            controls_frame,
            text="🎯 Auto-Layout",
            command=self._auto_layout
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            controls_frame,
            text="📊 Export Stats",
            command=self._export_stats
        ).pack(fill=tk.X, pady=2)
        
        # Legend
        legend_frame = ttk.LabelFrame(control_frame, text="Legend", padding=10)
        legend_frame.pack(fill=tk.X, padx=5, pady=5)
        
        legends = [
            ('🟢 Green', 'This is you'),
            ('🔵 Blue', 'Active peer'),
            ('🔴 Red', 'Offline peer'),
            ('───', 'Connection'),
            ('- - -', 'Weak connection')
        ]
        
        for label, desc in legends:
            frame = ttk.Frame(legend_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            ttk.Label(frame, text=desc).pack(side=tk.LEFT)
        
        # Log panel
        log_frame = ttk.LabelFrame(control_frame, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=10,
            bg='#0a0a1a',
            fg='#88ff88',
            font=('Consolas', 8),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def _start_update_loop(self):
        """Start topology update loop"""
        self._update_topology()
    
    def _update_topology(self):
        """Update topology from peer data"""
        if self.peer:
            try:
                # Get peer data
                nodes = {}
                
                # Add self node
                self_node = NetworkNode(
                    peer_id=self.peer.peer_id,
                    x=400,
                    y=300,
                    host=self.peer.host,
                    port=self.peer.port,
                    sites_count=len(self.peer.sites),
                    is_active=True,
                    is_self=True
                )
                nodes[self.peer.peer_id] = self_node
                
                # Add connected peers
                offset = 0
                for conn in self.peer.pin_wheel.get_all_peers():
                    angle = (offset / 8) * 2 * math.pi
                    radius = 200
                    
                    node = NetworkNode(
                        peer_id=conn.peer_id,
                        x=400 + radius * math.cos(angle),
                        y=300 + radius * math.sin(angle),
                        host=conn.host,
                        port=conn.port,
                        sites_count=conn.sites_count,
                        is_active=conn.is_connected,
                        latency=random.uniform(10, 100)
                    )
                    nodes[conn.peer_id] = node
                    
                    # Add connection to self
                    self.topology_canvas.add_connection(
                        NetworkConnection(
                            node1_id=self.peer.peer_id,
                            node2_id=conn.peer_id,
                            strength=0.8 if conn.is_connected else 0.3,
                            latency=node.latency,
                            is_active=conn.is_connected
                        )
                    )
                    
                    offset += 1
                
                # Update canvas
                self.topology_canvas.nodes = nodes
                self.topology_canvas.draw()
                
                # Update health metrics
                active_count = sum(1 for n in nodes.values() if n.is_active)
                self.health_panel.update_metrics({
                    'total_peers': len(nodes),
                    'active_peers': active_count,
                    'total_sites': sum(n.sites_count for n in nodes.values()),
                    'avg_latency': sum(n.latency for n in nodes.values()) / len(nodes) if nodes else 0,
                    'network_health': (active_count / len(nodes) * 100) if nodes else 0
                })
                
                # Update status indicators
                self.health_panel.set_status('ddns', True)
                self.health_panel.set_status('p2p', active_count > 0)
                self.health_panel.set_status('sync', True)
                
            except Exception as e:
                logger.error(f"Topology update error: {e}")
        
        # Schedule next update
        self.after(5000, self._update_topology)
    
    def _refresh_topology(self):
        """Manually refresh topology"""
        self.topology_canvas.connections.clear()
        self._update_topology()
        self._log("Topology refreshed")
    
    def _auto_layout(self):
        """Auto-layout nodes"""
        nodes = list(self.topology_canvas.nodes.values())
        if not nodes:
            return
        
        # Place self in center
        for node in nodes:
            if node.is_self:
                node.x = 400
                node.y = 300
            else:
                # Arrange others in circle
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(150, 250)
                node.x = 400 + radius * math.cos(angle)
                node.y = 300 + radius * math.sin(angle)
        
        self.topology_canvas.draw()
        self._log("Auto-layout applied")
    
    def _export_stats(self):
        """Export network statistics"""
        stats = {
            'timestamp': time.time(),
            'total_peers': len(self.topology_canvas.nodes),
            'active_peers': sum(1 for n in self.topology_canvas.nodes.values() if n.is_active),
            'total_sites': sum(n.sites_count for n in self.topology_canvas.nodes.values()),
            'connections': len(self.topology_canvas.connections)
        }
        
        import json
        stats_json = json.dumps(stats, indent=2)
        
        # Show in dialog
        dialog = tk.Toplevel(self)
        dialog.title("Network Statistics")
        dialog.geometry("400x300")
        
        text = tk.Text(dialog, bg='#0a0a1a', fg='#00ff88', font=('Consolas', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', stats_json)
        
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=5)
        
        self._log("Statistics exported")
    
    def _log(self, message: str):
        """Add log entry"""
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)


# Test the visualization
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    
    window = NetworkTopologyWindow(root)
    root.mainloop()
