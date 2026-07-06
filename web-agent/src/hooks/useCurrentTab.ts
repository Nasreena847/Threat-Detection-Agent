import { useQuery } from '@tanstack/react-query'
import { getCurrentTab } from '../services/chrome'

export function useCurrentTab() {
  return useQuery({
    queryKey: ['current-tab'],
    queryFn: getCurrentTab,
    staleTime: 10_000,
    retry: false,
  })
}
