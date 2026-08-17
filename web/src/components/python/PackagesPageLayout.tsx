import {Link} from '@tanstack/react-router'
import {Hero} from "#/components/core/Hero.tsx";
import {Breadcrumbs, Container, Stack} from "@mantine/core";
import {IconHomeFilled} from "@tabler/icons-react";
import {PackagesView} from "#/components/python/PackagesView.tsx";

export function PackagesPageLayout({page}: { page?: number }) {
    const breadcrumbItems = [
        {title: <IconHomeFilled size={18}/>, href: '/'},
        {title: 'Packages', href: '/project/'},
    ].map((item, index) => (
        <Link to={item.href} key={index}>
            {item.title}
        </Link>
    ));

    return (
        <>
            <Hero/>
            <div>
                <Container size={1200} pt={40} pb={40}>
                    <Stack>
                        <Breadcrumbs>{breadcrumbItems}</Breadcrumbs>
                        <PackagesView viewType={"grid"} initialPageSize={24} page={page}/>
                    </Stack>
                </Container>
            </div>
        </>
    )
}
