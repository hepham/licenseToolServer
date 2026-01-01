import { useEffect, useState } from 'react'
import { licenseApi, deviceApi, License, Device } from '../api/licenses'

export default function Dashboard() {
  const [licenses, setLicenses] = useState<License[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([licenseApi.list(), deviceApi.list()])
      .then(([licensesRes, devicesRes]) => {
        setLicenses(licensesRes.data)
        setDevices(devicesRes.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <span className="loading-spinner w-8 h-8" />
          <span className="text-slate-400">Loading dashboard...</span>
        </div>
      </div>
    )
  }

  const stats = {
    total: licenses.length,
    active: licenses.filter((l) => l.status === 'active').length,
    inactive: licenses.filter((l) => l.status === 'inactive').length,
    revoked: licenses.filter((l) => l.status === 'revoked').length,
    devices: devices.length,
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="page-title">Dashboard</h1>
        <p className="text-slate-400 mt-1">License management overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Licenses"
          value={stats.total}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          }
          color="cyan"
          delay={0}
        />
        <StatCard
          title="Active"
          value={stats.active}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="emerald"
          delay={75}
        />
        <StatCard
          title="Inactive"
          value={stats.inactive}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="slate"
          delay={150}
        />
        <StatCard
          title="Revoked"
          value={stats.revoked}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          }
          color="rose"
          delay={225}
        />
        <StatCard
          title="Devices"
          value={stats.devices}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
          color="amber"
          delay={300}
        />
      </div>
    </div>
  )
}

type ColorType = 'cyan' | 'emerald' | 'slate' | 'rose' | 'amber'

function StatCard({
  title,
  value,
  icon,
  color,
  delay,
}: {
  title: string
  value: number
  icon: React.ReactNode
  color: ColorType
  delay: number
}) {
  const colorConfig: Record<ColorType, { bg: string; text: string; glow: string; border: string }> = {
    cyan: {
      bg: 'from-cyan-500/20 to-cyan-600/5',
      text: 'text-cyan-400',
      glow: 'group-hover:shadow-glow-cyan',
      border: 'border-cyan-500/20',
    },
    emerald: {
      bg: 'from-emerald-500/20 to-emerald-600/5',
      text: 'text-emerald-400',
      glow: 'group-hover:shadow-glow-emerald',
      border: 'border-emerald-500/20',
    },
    slate: {
      bg: 'from-slate-500/20 to-slate-600/5',
      text: 'text-slate-400',
      glow: '',
      border: 'border-slate-500/20',
    },
    rose: {
      bg: 'from-rose-500/20 to-rose-600/5',
      text: 'text-rose-400',
      glow: 'group-hover:shadow-glow-rose',
      border: 'border-rose-500/20',
    },
    amber: {
      bg: 'from-amber-500/20 to-amber-600/5',
      text: 'text-amber-400',
      glow: 'group-hover:shadow-glow-amber',
      border: 'border-amber-500/20',
    },
  }

  const config = colorConfig[color]

  return (
    <div
      className={`stat-card group animate-slide-up transition-all duration-300 hover:scale-[1.02] ${config.glow} ${config.border}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Gradient overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${config.bg} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
      
      {/* Content */}
      <div className="relative z-10">
        <div className={`${config.text} mb-3`}>{icon}</div>
        <div className="text-4xl font-bold text-slate-100 tracking-tight">{value}</div>
        <div className="text-sm text-slate-400 mt-1 font-medium">{title}</div>
      </div>
    </div>
  )
}
