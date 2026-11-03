import { PRICE_MONTHLY, PRICE_YEARLY } from '../config'
import type { PricingPlan } from '../types'

export const mockPlans: PricingPlan[] = [
  { id: 'monthly', name: 'Monthly', price: PRICE_MONTHLY, interval: 'month' },
  { id: 'yearly', name: 'Yearly', price: PRICE_YEARLY, interval: 'year' },
]
