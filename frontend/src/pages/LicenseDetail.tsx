import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { licenseApi, License } from '../api/licenses'

export default function LicenseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [license, setLicense] = useState<License | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [revoking, setRevoking] = useState(false)

  useEffect(() => {
    if (id) {
      licenseApi
        .get(parseInt(id))
        .then((res) => setLicense(res.data))
        .catch(() => setError('Failed to load license'))
        .finally(() => setLoading(false))
    }
  }, [id])

  const handleRevoke = async () => {
    if (!license || !confirm('Are you sure you want to revoke this license?')) return
    setRevoking(true)
    try {
      await licenseApi.revoke(license.id)
      setLicense({ ...license, status: 'revoked', device: undefined })
    } catch {
      setError('Failed to revoke license')
    } finally {
      setRevoking(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <span className="loading-spinner w-8 h-8" />
          <span className="text-slate-400">Loading license...</span>
        </div>
      </div>
    )
  }

  if (error || !license) {
    return (
      <div className="error-alert animate-slide-down">
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm">{error || 'License not found'}</span>
      </div>
    )
  }

  const statusConfig: Record<string, { class: string; dot: string; label: string }> = {
    active: { class: 'status-active', dot: 'bg-emerald-400', label: 'Active' },
    inactive: { class: 'status-inactive', dot: 'bg-slate-400', label: 'Inactive' },
    revoked: { class: 'status-revoked', dot: 'bg-rose-400', label: 'Revoked' },
  }

  const status = statusConfig[license.status]

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <button
        onClick={() => navigate('/licenses')}
        className="btn-ghost mb-6 -ml-2 flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Licenses
      </button>

      {/* Main card */}
      <div className="glass-card overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-700/50">
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className={status.class}>
                  <span className={`glow-dot ${status.dot}`} />
                  {status.label}
                </span>
              </div>
              <h1 className="font-mono text-2xl text-cyan-400 bg-cyan-500/10 px-4 py-2 rounded-xl inline-block">
                {license.key}
              </h1>
            </div>
            {license.status !== 'revoked' && (
              <button onClick={handleRevoke} disabled={revoking} className="btn-danger flex items-center gap-2">
                {revoking ? (
                  <>
                    <span className="loading-spinner" />
                    <span>Revoking...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                    <span>Revoke License</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1">
            <label className="label">Created</label>
            <p className="text-slate-100 font-medium">
              {new Date(license.created_at).toLocaleString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
          <div className="space-y-1">
            <label className="label">Last Updated</label>
            <p className="text-slate-100 font-medium">
              {new Date(license.updated_at).toLocaleString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
        </div>

        {/* Device section */}
        <div className="p-6 border-t border-slate-700/50">
          <h2 className="section-title flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Device Information
          </h2>
          {license.device ? (
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-1">
                  <label className="label">Device ID</label>
                  <p className="font-mono text-sm text-cyan-400 bg-cyan-500/10 px-3 py-2 rounded-lg break-all">
                    {license.device.device_id}
                  </p>
                </div>
                <div className="space-y-1">
                  <label className="label">Activated At</label>
                  <p className="text-slate-100 font-medium">
                    {new Date(license.device.activated_at).toLocaleString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/30 rounded-xl p-8 border border-slate-700/30 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-slate-400">No device activated</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
