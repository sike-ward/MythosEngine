export const SkeletonLine = ({ width = 'w-full', height = 'h-4' }) => (
  <div className={`${width} ${height} bg-gray-200/20 rounded animate-pulse mb-2`} />
)

export const SkeletonCard = () => (
  <div className="p-4 border border-txt-muted/10 rounded-xl">
    <SkeletonLine width="w-3/4" height="h-5" />
    <SkeletonLine />
    <SkeletonLine width="w-5/6" />
  </div>
)

export const SkeletonStatCard = () => (
  <div className="p-6 border border-txt-muted/10 rounded-xl flex flex-col gap-3">
    <SkeletonLine width="w-8" height="h-8" />
    <SkeletonLine width="w-1/2" height="h-3" />
    <SkeletonLine width="w-1/3" height="h-8" />
  </div>
)
