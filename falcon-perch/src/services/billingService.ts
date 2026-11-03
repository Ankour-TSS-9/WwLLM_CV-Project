import { mockPlans } from '../mock/billing'
import type { PricingPlan } from '../types'

export async function getPlans(): Promise<PricingPlan[]> {
  return mockPlans
}

export async function startCheckout(_planId: PricingPlan['id']): Promise<{ started: false }> {
  return { started: false }
}
