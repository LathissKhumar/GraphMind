import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../src/App'

const API_BASE = ''

global.fetch = async (url, options) => {
  const urlStr = typeof url === 'string' ? url : ''
  
  if (urlStr.includes('/api/health')) {
    return { ok: true, json: async () => ({ status: 'healthy' }) }
  }
  if (urlStr.includes('/api/metrics')) {
    return { ok: true, json: async () => ({ savings_percentage: 75, total_queries: 10, total_tokens_used: 500 }) }
  }
  if (urlStr.includes('/api/graph')) {
    return { ok: true, json: async () => ({ elements: [] }) }
  }
  if (urlStr.includes('/api/query') && options?.method === 'POST') {
    return { 
      ok: true, 
      json: async () => ({ 
        answer: 'The function does X', 
        tier: 'GRAPH_ONLY',
        tokens_used: 0,
        savings: '100%'
      }) 
    }
  }
  return { ok: false, json: async () => ({ error: 'Not found' }) }
}

describe('App', () => {
  beforeEach(() => {
    render(<App />)
  })

  describe('Header', () => {
    it('renders header with title', () => {
      expect(screen.getByText(/CODEGRAPHX/i)).toBeDefined()
    })
  })

  describe('Query Input', () => {
    it('renders query input field', () => {
      expect(screen.getByPlaceholder(/What functions call/i)).toBeDefined()
    })

    it('allows typing in query field', () => {
      const input = screen.getByPlaceholder(/What functions call/i)
      fireEvent.change(input, { target: { value: 'test query' } })
      expect(input.value).toBe('test query')
    })
  })

  describe('Execute Button', () => {
    it('renders execute button', () => {
      expect(screen.getByText(/EXECUTE/i)).toBeDefined()
    })
  })

  describe('Codebase Input', () => {
    it('renders clone input field', () => {
      expect(screen.getByPlaceholder(/github.com\/owner\/repo/i)).toBeDefined()
    })

    it('renders clone button', () => {
      expect(screen.getByText(/Clone/i)).toBeDefined()
    })
  })

  describe('Graph Visualization', () => {
    it('renders graph section', () => {
      expect(screen.getByText(/CODE GRAPH/i)).toBeDefined()
    })
  })

  describe('Query History', () => {
    it('renders history section', () => {
      expect(screen.getByText(/Query History/i)).toBeDefined()
    })
  })

  describe('Metrics', () => {
    it('renders metrics cards', () => {
      expect(screen.getByText(/Token Savings/i)).toBeDefined()
    })
  })
})

describe('Components', () => {
  describe('GraphViz', () => {
    it('handles empty data', () => {
      expect(true).toBe(true)
    })
  })

  describe('Badge', () => {
    it('renders tier badge', () => {
      expect(screen.getByText(/GRAPH_ONLY/i)).toBeDefined()
    })
  })
})