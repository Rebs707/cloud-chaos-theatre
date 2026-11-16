
export type ServiceState =
  | 'healthy'
  | 'degraded'
  | 'down'
  | 'recovering'

export type ScenarioRequest = {
  id: string
  name: string
  description: string
  targetService: string
  startStep: number
}

export type IncidentRequest = {
  topology: {
    services: {
      id: string
      name: string
    }[]
    edges: {
      dependent: string
      dependency: string
      criticality: 'hard' | 'soft'
    }[]
  }
  initial_snapshot: {
    step: number
    services: {
      service_id: string
      state: ServiceState
      recovery_counter: number
    }[]
  }
  faults: {
    service_id: string
    start_step: number
  }[]
  config: {
    recovery_duration: number
    max_steps: number
    seed: number
  }
}

export type IncidentResponse = {
  simulation: {
    snapshots: {
      step: number
      services: {
        service_id: string
        state: ServiceState
        recovery_counter: number
      }[]
    }[]
    events: {
      step: number
      kind: string
      service_id: string
      description: string
    }[]
    termination_reason: string
  }
  diagnosis: Record<string, unknown>
  recovery_plan: Record<string, unknown>
  commentary: Record<string, unknown>
}

const topology: IncidentRequest['topology'] = {
  services: [
    { id: 'worker', name: 'Worker Service' },
    { id: 'api', name: 'API Service' },
    { id: 'database', name: 'Database' },
  ],
  edges: [
    {
      dependent: 'worker',
      dependency: 'api',
      criticality: 'hard',
    },
    {
      dependent: 'api',
      dependency: 'database',
      criticality: 'hard',
    },
  ],
}

export async function analyzeIncident(
  scenario: ScenarioRequest,
): Promise<IncidentResponse> {
  const requestBody: IncidentRequest = {
    topology,
    initial_snapshot: {
      step: 0,
      services: [
        {
          service_id: 'worker',
          state: 'healthy',
          recovery_counter: 0,
        },
        {
          service_id: 'api',
          state: 'healthy',
          recovery_counter: 0,
        },
        {
          service_id: 'database',
          state: 'healthy',
          recovery_counter: 0,
        },
      ],
    },
    faults: [
      {
        service_id: scenario.targetService,
        start_step: scenario.startStep,
      },
    ],
    config: {
      recovery_duration: 1,
      max_steps: 100,
      seed: 0,
    },
  }

  const response = await fetch('/api/incidents/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  })

  if (!response.ok) {
    const errorMessage = await response.text()
    throw new Error(
      `Incident analysis failed (${response.status}): ${errorMessage}`,
    )
  }

  return (await response.json()) as IncidentResponse
}

