import {createFileRoute} from '@tanstack/react-router'
import {PackagesPageLayout} from "#/components/python/PackagesPageLayout.tsx";

export const Route = createFileRoute('/project/')({
    component: RouteComponent,
})

function RouteComponent() {
    return <PackagesPageLayout />
}
