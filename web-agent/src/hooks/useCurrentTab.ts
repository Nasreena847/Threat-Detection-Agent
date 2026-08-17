import { useQuery } from '@tanstack/react-query'
import { getCurrentTab } from '../services/chrome'

export function useCurrentTab() {
  return useQuery({
    queryKey: ['current-tab'],
    queryFn: getCurrentTab,
    staleTime: 0,
    refetchOnMount: 'always',
    retry: false,
  })
}
