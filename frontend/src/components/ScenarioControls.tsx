
type Scenario = {
  id: string
  name: string
  description: string
  targetService: string
  startStep: number
}

const scenarios: Scenario[] = [
  {
    id: 'database-outage',
    name: 'Database Outage',
    description: 'Simulate a database failure and observe cascading impact.',
    targetService: 'database',
    startStep: 1,
  },
  {
    id: 'api-outage',
    name: 'API Service Outage',
    description: 'Take the API service offline and observe worker impact.',
    targetService: 'api',
    startStep: 1,
  },
  {
    id: 'worker-outage',
    name: 'Worker Service Outage',
    description: 'Simulate an isolated worker service failure.',
    targetService: 'worker',
    startStep: 1,
  },
]

type ScenarioControlsProps = {
  onRunScenario: (scenario: Scenario) => void
  disabled?: boolean
}

function ScenarioControls({
  onRunScenario,
  disabled = false,
}: ScenarioControlsProps) {
  return (
    <div className="scenario-list">
      {scenarios.map((scenario) => (
        <article className="scenario-card" key={scenario.id}>
          <div className="scenario-card-heading">
            <span className="scenario-indicator" />
            <strong>{scenario.name}</strong>
          </div>

          <p>{scenario.description}</p>

          <div className="scenario-target">
            TARGET: {scenario.targetService.toUpperCase()}
          </div>

          <button
            className="primary-button scenario-button"
            disabled={disabled}
            onClick={() => onRunScenario(scenario)}
          >
            Run Scenario
          </button>
        </article>
      ))}
    </div>
  )
}

export type { Scenario }
export default ScenarioControls
