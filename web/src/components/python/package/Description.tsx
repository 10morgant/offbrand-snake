import {Box} from '@mantine/core'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import {useEffect, useMemo, useRef} from 'react'

export function Description({generated}: { generated?: string }) {
    const contentRef = useRef<HTMLDivElement>(null)

    const sanitizedDescription = useMemo(
        () => (generated ? DOMPurify.sanitize(generated) : ''),
        [generated]
    )

    useEffect(() => {
        if (!contentRef.current) return

        contentRef.current.querySelectorAll('pre code').forEach((block) => {
            const classNames = [
                ...block.classList,
                ...(block.closest('pre')?.classList ?? []),
            ]
            const language = classNames
                .map((className) => className.startsWith('language-')
                    ? className.slice('language-'.length)
                    : className
                )
                .find((className) => hljs.getLanguage(className))

            if (!language) return

            block.innerHTML = hljs.highlight(block.textContent ?? '', {
                language,
                ignoreIllegals: true,
            }).value
            block.classList.add('hljs')
        })
    }, [sanitizedDescription])

    return (
        <Box
            ref={contentRef}
            className="package-description"
            dangerouslySetInnerHTML={{__html: sanitizedDescription}}
        />
    )
}