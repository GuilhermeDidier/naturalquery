// frontend/src/components/Results/SqlBlock.tsx
import { useEffect, useRef } from 'react'
import hljs from 'highlight.js/lib/core'
import sql from 'highlight.js/lib/languages/sql'
import 'highlight.js/styles/atom-one-dark.css'

hljs.registerLanguage('sql', sql)

interface Props {
  sql: string
}

export function SqlBlock({ sql: sqlText }: Props) {
  const codeRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (codeRef.current && !codeRef.current.dataset.highlighted) {
      hljs.highlightElement(codeRef.current)
    }
  }, [sqlText])

  return (
    <details className="sql-toggle">
      <summary>View generated SQL</summary>
      <pre className="sql-block">
        <code ref={codeRef} className="language-sql">
          {sqlText}
        </code>
      </pre>
    </details>
  )
}
