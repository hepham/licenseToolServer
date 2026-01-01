import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { licenseApi, License } from '../api/licenses'

export default function Licenses() {
  const [licenses, setLicenses] = useState<License[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  const fetchLicenses = () => {
    setLoading(true)
    licenseApi
      .list()
      .then((res) => setLicenses(res.data))
      .catch(() => setError('Failed to load licenses'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchLicenses()
  }, [])

  const handleCreate = async () => {
    setCreating(true)
    try {
      await licenseApi.create()
      fetchLicenses()
    } catch {
      setError('Failed to create license')
    } finally {
      setCreating(false)
    }
  }

  const statusBadge = (status: string) => {
    const classes: Record<string, string> = {
      active: 'status-active',
      inactive: 'status-inactive',
      revoked: 'status-revoked',
    }
    const dots: Record<string, string> = {
      active: 'bg-emerald-400',
      inactive: 'bg-slate-400',
      revoked: 'bg-rose-400',
    }
    return (
      <span className={classes[status]}>
        <span className={`glow-dot ${dots[status]}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <span className="loading-spinner w-8 h-8" />
          <span className="text-slate-400">Loading licenses...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="page-title">Licenses</h1>
          <p className="text-slate-400 mt-1">{licenses.length} total licenses</p>
        </div>
        <button onClick={handleCreate} disabled={creating} className="btn-primary flex items-center gap-2">
          {creating ? (
            <>
              <span className="loading-spinner" />
              <span>Creating...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Generate License</span>
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="error-alert mb-6 animate-slide-down">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-rose-400 hover:text-rose-300">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="table-header">License Key</th>
                <th className="table-header">Status</th>
                <th className="table-header">Created</th>
                <th className="table-header text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {licenses.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center">
                        <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                      </div>
                      <p className="text-slate-400">No licenses found</p>
                      <button onClick={handleCreate} className="btn-primary text-sm">
                        Generate your first license
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                licenses.map((license, idx) => (
                  <tr
                    key={license.id}
                    className="hover:bg-slate-800/30 transition-colors duration-150 animate-slide-up"
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <td className="table-cell">
                      <span className="font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1.5 rounded-lg text-sm">
                        {license.key}
                      </span>
                    </td>
                    <td className="table-cell">{statusBadge(license.status)}</td>
                    <td className="table-cell text-slate-400">
                      {new Date(license.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="table-cell text-right">
                      <Link
                        to={`/licenses/${license.id}`}
                        className="inline-flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 transition-colors font-medium text-sm"
                      >
                        View Details
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
