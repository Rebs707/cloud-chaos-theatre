
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { ServiceState } from '../services/incidentApi'

type ServiceStatus = {
  service_id: string
  state: ServiceState
}

type InfrastructureTopologyProps = {
  serviceStates?: ServiceStatus[]
}

const services = [
  {
    id: 'worker',
    name: 'Worker Service',
    position: { x: 80, y: 40 },
  },
  {
    id: 'api',
    name: 'API Service',
    position: { x: 80, y: 190 },
  },
  {
    id: 'database',
    name: 'Database',
    position: { x: 80, y: 340 },
  },
]

const stateStyles: Record<
  ServiceState,
  { border: string; background: string; label: string }
> = {
  healthy: {
    border: '#36c98f',
    background: '#142820',
    label: 'HEALTHY',
  },
  degraded: {
    border: '#f5ad42',
    background: '#332819',
    label: 'DEGRADED',
  },
  down: {
    border: '#ef5350',
    background: '#351b20',
    label: 'DOWN',
  },
  recovering: {
    border: '#f5ad42',
    background: '#332819',
    label: 'RECOVERING',
  },
}

const initialEdges: Edge[] = [
  {
    id: 'worker-api',
    source: 'worker',
    target: 'api',
    label: 'depends on',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#43c8e8',
    },
    style: { stroke: '#43c8e8', strokeWidth: 2 },
    labelStyle: { fill: '#8491a5', fontSize: 10 },
  },
  {
    id: 'api-database',
    source: 'api',
    target: 'database',
    label: 'depends on',
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#43c8e8',
    },
    style: { stroke: '#43c8e8', strokeWidth: 2 },
    labelStyle: { fill: '#8491a5', fontSize: 10 },
  },
]

function InfrastructureTopology({
  serviceStates = [],
}: InfrastructureTopologyProps) {
  const nodes: Node[] = services.map((service) => {
    const currentState =
      serviceStates.find(
        (item) => item.service_id === service.id,
      )?.state ?? 'healthy'

    const appearance = stateStyles[currentState]

    return {
      id: service.id,
      position: service.position,
      data: {
        label: `${service.name} · ${appearance.label}`,
      },
      style: {
        width: 180,
        padding: 18,
        border: `1px solid ${appearance.border}`,
        borderRadius: 9,
        background: appearance.background,
        color: '#e5eaf2',
        fontSize: 13,
        fontWeight: 600,
        textAlign: 'center',
      },
    }
  })

  return (
    <div style={{ width: '100%', height: 390 }}>
      <ReactFlow
        nodes={nodes}
        edges={initialEdges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
      >
        <Background color="#344155" gap={20} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export default InfrastructureTopology

