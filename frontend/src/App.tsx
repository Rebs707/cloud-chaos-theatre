
import { useState } from 'react'
import './App.css'
import InfrastructureTopology from './components/InfrastructureTopology'
import ScenarioControls, {
  type Scenario,
} from './components/ScenarioControls'
import {
  analyzeIncident,
  type IncidentResponse,
} from './services/incidentApi'

type DisplayRecord = Record<string, unknown>

function displayValue(value: unknown, fallback = 'Not available') {
  return typeof value === 'string' && value.length > 0
    ? value
    : fallback
}

function formatEventKind(kind: string) {
  return kind
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function getEventColor(kind: string) {
  if (kind.includes('FAULT')) return '#ef5350'
  if (kind.includes('RECOVERY')) return '#f5ad42'
  return '#43c8e8'
}

function getStateColor(state: string) {
  switch (state.toLowerCase()) {
    case 'down':
      return '#ef5350'
    case 'degraded':
    case 'recovering':
      return '#f5ad42'
    default:
      return '#36c98f'
  }
}

function App() {
  const [selectedScenario, setSelectedScenario] =
    useState<Scenario | null>(null)

  const [incidentResult, setIncidentResult] =
    useState<IncidentResponse | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleRunScenario(scenario: Scenario) {
    setSelectedScenario(scenario)
    setIsLoading(true)
    setError(null)
    setIncidentResult(null)

    try {
      const result = await analyzeIncident(scenario)
      setIncidentResult(result)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  function handleResetSimulation() {
    if (isLoading) return

    setIncidentResult(null)
    setSelectedScenario(null)
    setError(null)
  }

  function handleReplayScenario() {
    if (isLoading || !selectedScenario) return

    void handleRunScenario(selectedScenario)
  }

  const latestSnapshot =
    incidentResult?.simulation.snapshots.at(-1)

  const totalServices =
    latestSnapshot?.services.length ?? 3

  const healthyServices =
    latestSnapshot?.services.filter(
      (service) => service.state === 'healthy',
    ).length ?? 3

  const activeIncidents = incidentResult ? 1 : 0
  const simulationStep = latestSnapshot?.step ?? 0

  const metrics = [
    {
      label: 'TOTAL SERVICES',
      value: String(totalServices).padStart(2, '0'),
      note: 'Infrastructure components',
      color: 'var(--text)',
    },
    {
      label: 'HEALTHY SERVICES',
      value: String(healthyServices).padStart(2, '0'),
      note:
        healthyServices === totalServices
          ? 'All systems operational'
          : `${totalServices - healthyServices} service(s) affected`,
      color: 'var(--green)',
    },
    {
      label: 'ACTIVE INCIDENTS',
      value: String(activeIncidents).padStart(2, '0'),
      note: incidentResult
        ? 'Incident analysis completed'
        : 'No active incidents',
      color: 'var(--amber)',
    },
    {
      label: 'SIMULATION STEP',
      value: String(simulationStep).padStart(2, '0'),
      note: incidentResult
        ? 'Latest simulation step'
        : 'Awaiting scenario execution',
      color: 'var(--cyan)',
    },
  ]

  const diagnosis = incidentResult?.diagnosis as
    | DisplayRecord
    | undefined

  const recoveryPlan = incidentResult?.recovery_plan as
    | DisplayRecord
    | undefined

  const commentary = incidentResult?.commentary as
    | DisplayRecord
    | undefined

  const rootCauses = Array.isArray(diagnosis?.root_causes)
    ? (diagnosis.root_causes as DisplayRecord[])
    : []

  const affectedServices = Array.isArray(diagnosis?.affected_services)
    ? (diagnosis.affected_services as DisplayRecord[])
    : []

  const evidence = Array.isArray(diagnosis?.evidence)
    ? (diagnosis.evidence as DisplayRecord[])
    : []

  const recommendations = Array.isArray(recoveryPlan?.recommendations)
    ? (recoveryPlan.recommendations as DisplayRecord[])
    : []

  const keyFindings = Array.isArray(commentary?.key_findings)
    ? (commentary.key_findings as string[])
    : []

  const immediateActions = Array.isArray(commentary?.immediate_actions)
    ? (commentary.immediate_actions as string[])
    : []

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <h1>Cloud Chaos Theatre</h1>
            <p>Infrastructure Failure Simulation Platform</p>
          </div>
        </div>

        <div className="header-actions">
          <div className="environment-label">
            <span className="status-dot" />
            SIMULATED ENVIRONMENT
          </div>
          <div className="connection-status">
            <span className="status-dot" />
            LOCAL MODE
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        <section className="page-heading">
          <div>
            <div className="eyebrow">OPERATIONS CONTROL CENTRE</div>
            <h2>Infrastructure Overview</h2>
            <p>
              Monitor service health, simulate failures and investigate
              cascading infrastructure incidents.
            </p>
          </div>

          <div className="simulation-badge">
            <span className="status-dot" />
            {isLoading ? 'SIMULATION RUNNING' : 'SYSTEM READY'}
          </div>
        </section>

        <section className="metrics-grid">
          {metrics.map((metric) => (
            <article className="metric-card" key={metric.label}>
              <div className="metric-label">{metric.label}</div>
              <div
                className="metric-value"
                style={{ color: metric.color }}
              >
                {metric.value}
              </div>
              <div className="metric-note">{metric.note}</div>
            </article>
          ))}
        </section>

        <section className="dashboard-grid">
          <div className="main-column">
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h3>Infrastructure Topology</h3>
                  <span className="panel-subtitle">
                    SERVICE DEPENDENCY MAP
                  </span>
                </div>
                <span className="panel-subtitle">
                  {totalServices} SERVICES
                </span>
              </div>

              <InfrastructureTopology
                serviceStates={latestSnapshot?.services ?? []}
              />
            </section>

            <section className="panel timeline-panel">
              <div className="panel-header">
                <div>
                  <h3>Incident Timeline</h3>
                  <span className="panel-subtitle">
                    SIMULATION EVENTS
                  </span>
                </div>
                <span className="panel-subtitle">
                  {incidentResult
                    ? `STEP ${String(simulationStep).padStart(2, '0')}`
                    : 'STEP 00'}
                </span>
              </div>

              <div style={{ padding: '18px 20px' }}>
                {incidentResult &&
                incidentResult.simulation.events.length > 0 ? (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '18px',
                    }}
                  >
                    {incidentResult.simulation.events.map(
                      (event, index) => (
                        <div
                          key={`${event.step}-${event.service_id}-${event.kind}-${index}`}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '52px 12px minmax(0, 1fr)',
                            gap: '12px',
                            alignItems: 'start',
                          }}
                        >
                          <span
                            style={{
                              color: 'var(--cyan)',
                              fontSize: '12px',
                              fontWeight: 700,
                              paddingTop: '2px',
                            }}
                          >
                            STEP {String(event.step).padStart(2, '0')}
                          </span>

                          <span
                            style={{
                              width: '9px',
                              height: '9px',
                              marginTop: '4px',
                              borderRadius: '50%',
                              background: getEventColor(event.kind),
                              boxShadow: `0 0 9px ${getEventColor(event.kind)}66`,
                            }}
                          />

                          <div style={{ minWidth: 0 }}>
                            <div
                              style={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '8px',
                                alignItems: 'center',
                                marginBottom: '5px',
                              }}
                            >
                              <strong
                                style={{
                                  color: 'var(--text)',
                                  fontSize: '13px',
                                }}
                              >
                                {formatEventKind(event.kind)}
                              </strong>

                              <span
                                style={{
                                  color: 'var(--cyan)',
                                  fontSize: '11px',
                                  fontWeight: 600,
                                }}
                              >
                                {event.service_id.toUpperCase()}
                              </span>
                            </div>

                            <p
                              style={{
                                color: 'var(--muted)',
                                fontSize: '12px',
                                lineHeight: 1.6,
                                margin: 0,
                              }}
                            >
                              {event.description}
                            </p>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                ) : (
                  <div className="timeline-placeholder">
                    No simulation events yet. Run a failure scenario
                    to populate the incident timeline.
                  </div>
                )}
              </div>
            </section>
          </div>

          <aside className="side-column">
            <section className="panel">
              <div className="panel-header">
                <h3>Failure Scenarios</h3>
              </div>

              <div className="panel-body">
                <ScenarioControls
                  onRunScenario={handleRunScenario}
                  disabled={isLoading}
                />

                <div
                  style={{
                    display: 'flex',
                    gap: '9px',
                    marginTop: '14px',
                    flexWrap: 'wrap',
                  }}
                >
                  <button
                    type="button"
                    onClick={handleReplayScenario}
                    disabled={isLoading || !selectedScenario}
                    style={{
                      flex: '1 1 110px',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      background: 'rgba(67, 200, 232, 0.10)',
                      color: 'var(--cyan)',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor:
                        isLoading || !selectedScenario
                          ? 'not-allowed'
                          : 'pointer',
                      opacity:
                        isLoading || !selectedScenario ? 0.45 : 1,
                    }}
                  >
                    {isLoading ? 'RUNNING...' : '↻ Replay Scenario'}
                  </button>

                  <button
                    type="button"
                    onClick={handleResetSimulation}
                    disabled={isLoading}
                    style={{
                      flex: '1 1 110px',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      background: 'rgba(239, 83, 80, 0.08)',
                      color: 'var(--text)',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      opacity: isLoading ? 0.45 : 1,
                    }}
                  >
                    ↺ Reset Simulation
                  </button>
                </div>

                {selectedScenario && (
                  <div className="empty-state">
                    {isLoading ? (
                      'Running simulation...'
                    ) : incidentResult ? (
                      <>
                        Simulation completed: {selectedScenario.name}
                        <br />
                        Termination:{' '}
                        {incidentResult.simulation.termination_reason}
                      </>
                    ) : error ? (
                      'Simulation could not be completed.'
                    ) : (
                      `Selected: ${selectedScenario.name}`
                    )}
                  </div>
                )}

                {error && (
                  <div className="empty-state down-text" role="alert">
                    {error}
                  </div>
                )}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h3>Incident Commander</h3>
              </div>

              <div className="panel-body">
                {incidentResult ? (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '18px',
                    }}
                  >
                    <div>
                      <div className="eyebrow">INCIDENT BRIEFING</div>
                      <h3 style={{ marginTop: '8px' }}>
                        {displayValue(
                          commentary?.headline,
                          'Incident analysis complete',
                        )}
                      </h3>
                      <p
                        style={{
                          color: 'var(--muted)',
                          fontSize: '13px',
                          lineHeight: 1.6,
                        }}
                      >
                        {displayValue(commentary?.summary)}
                      </p>
                    </div>

                    <div>
                      <div className="eyebrow">ROOT-CAUSE DIAGNOSIS</div>
                      <p
                        style={{
                          color: 'var(--muted)',
                          fontSize: '13px',
                          lineHeight: 1.6,
                        }}
                      >
                        {displayValue(diagnosis?.summary)}
                      </p>

                      {rootCauses.map((cause, index) => (
                        <div
                          key={`${String(cause.service_id)}-${index}`}
                          style={{
                            padding: '12px',
                            marginTop: '10px',
                            border: '1px solid var(--border)',
                            borderRadius: '8px',
                          }}
                        >
                          <strong style={{ color: '#ef5350' }}>
                            {displayValue(cause.service_name)}
                          </strong>
                          <p
                            style={{
                              color: 'var(--muted)',
                              fontSize: '12px',
                              lineHeight: 1.6,
                            }}
                          >
                            {displayValue(cause.explanation)}
                          </p>
                          <span className="panel-subtitle">
                            {formatEventKind(
                              displayValue(cause.cause_kind, 'ROOT CAUSE'),
                            )}
                          </span>
                        </div>
                      ))}
                    </div>

                    <div>
                      <div className="eyebrow">AFFECTED SERVICES</div>
                      {affectedServices.length > 0 ? (
                        affectedServices.map((service, index) => {
                          const state = displayValue(
                            service.current_state,
                            'unknown',
                          )

                          return (
                            <div
                              key={`${String(service.service_id)}-${index}`}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                gap: '10px',
                                padding: '9px 0',
                                borderBottom: '1px solid var(--border)',
                              }}
                            >
                              <span style={{ fontSize: '13px' }}>
                                {displayValue(service.service_name)}
                              </span>
                              <span
                                style={{
                                  color: getStateColor(state),
                                  fontSize: '11px',
                                  fontWeight: 700,
                                }}
                              >
                                {state.toUpperCase()}
                              </span>
                            </div>
                          )
                        })
                      ) : (
                        <p className="metric-note">
                          No affected services reported.
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="eyebrow">SUPPORTING EVIDENCE</div>
                      {evidence.length > 0 ? (
                        evidence.map((item, index) => (
                          <div
                            key={`${String(item.service_id)}-${String(item.step)}-${index}`}
                            style={{
                              padding: '9px 0',
                              borderBottom: '1px solid var(--border)',
                            }}
                          >
                            <span
                              style={{
                                color: 'var(--cyan)',
                                fontSize: '11px',
                                fontWeight: 700,
                              }}
                            >
                              STEP {String(item.step ?? 0).padStart(2, '0')} ·{' '}
                              {displayValue(item.service_id).toUpperCase()}
                            </span>
                            <p
                              style={{
                                color: 'var(--muted)',
                                fontSize: '12px',
                                lineHeight: 1.5,
                              }}
                            >
                              {displayValue(item.description)}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="metric-note">
                          No evidence references returned.
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="eyebrow">
                        PRIORITISED RECOVERY PLAN
                      </div>
                      <p
                        style={{
                          color: 'var(--muted)',
                          fontSize: '12px',
                          lineHeight: 1.5,
                        }}
                      >
                        {displayValue(recoveryPlan?.summary)}
                      </p>

                      {recommendations.length > 0 ? (
                        recommendations.map((item, index) => (
                          <div
                            key={`${String(item.service_id)}-${index}`}
                            style={{
                              padding: '12px',
                              marginTop: '9px',
                              border: '1px solid var(--border)',
                              borderRadius: '8px',
                            }}
                          >
                            <div
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                gap: '8px',
                              }}
                            >
                              <strong style={{ fontSize: '13px' }}>
                                {displayValue(item.service_name)}
                              </strong>
                              <span
                                style={{
                                  color: 'var(--cyan)',
                                  fontSize: '11px',
                                }}
                              >
                                PRIORITY {String(item.priority ?? index + 1)}
                              </span>
                            </div>
                            <p
                              style={{
                                color: 'var(--text)',
                                fontSize: '12px',
                                lineHeight: 1.5,
                              }}
                            >
                              {displayValue(item.action)}
                            </p>
                            <p
                              style={{
                                color: 'var(--muted)',
                                fontSize: '12px',
                                lineHeight: 1.5,
                              }}
                            >
                              {displayValue(item.reason)}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="metric-note">
                          No recovery recommendations returned.
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="eyebrow">KEY FINDINGS</div>
                      {keyFindings.length > 0 ? (
                        keyFindings.map((finding, index) => (
                          <p
                            key={index}
                            style={{
                              color: 'var(--muted)',
                              fontSize: '12px',
                              lineHeight: 1.5,
                            }}
                          >
                            {index + 1}. {finding}
                          </p>
                        ))
                      ) : (
                        <p className="metric-note">
                          No additional findings returned.
                        </p>
                      )}
                    </div>

                    <div>
                      <div className="eyebrow">IMMEDIATE ACTIONS</div>
                      {immediateActions.map((action, index) => (
                        <p
                          key={index}
                          style={{
                            color: 'var(--muted)',
                            fontSize: '12px',
                            lineHeight: 1.5,
                          }}
                        >
                          {index + 1}. {action}
                        </p>
                      ))}
                    </div>

                    <div
                      style={{
                        padding: '12px',
                        background: 'rgba(67, 200, 232, 0.06)',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                      }}
                    >
                      <div className="eyebrow">RECOVERY STATUS</div>
                      <p style={{ fontSize: '13px', lineHeight: 1.6 }}>
                        {displayValue(commentary?.recovery_status)}
                      </p>
                      <span className="panel-subtitle">
                        ANALYSIS SOURCE:{' '}
                        {displayValue(commentary?.source).toUpperCase()}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    Root-cause diagnosis, evidence and recovery
                    recommendations will appear here after a scenario runs.
                  </div>
                )}
              </div>
            </section>
          </aside>
        </section>
      </main>
    </div>
  )
}

export default App









