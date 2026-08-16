import {createFileRoute} from '@tanstack/react-router'
import {NamespacesPageLayout} from "#/components /python/NamespacesPageLayout.tsx";

export const Route = createFileRoute('/project/')({
    component: RouteComponent,
})

function RouteComponent() {
    return <NamespacesPageLayout />
}
