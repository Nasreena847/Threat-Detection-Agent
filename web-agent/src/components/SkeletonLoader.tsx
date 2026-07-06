export default function SkeletonLoader() {
  return (
    <div className="space-y-3">
      <div className="skeleton-block h-24" />
      <div className="skeleton-block h-44" />
      <div className="skeleton-block h-16" />
      <div className="space-y-2">
        <div className="skeleton-block h-12" />
        <div className="skeleton-block h-12" />
        <div className="skeleton-block h-12" />
      </div>
    </div>
  )
}
