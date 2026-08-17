import {createFileRoute, Link} from '@tanstack/react-router'
import {colourTheme} from "#/config/colours.ts";
import {
    ActionIcon,
    Box,
    Breadcrumbs,
    Button,
    Card,
    Code,
    Container,
    CopyButton,
    DataList,
    Divider,
    Flex,
    Group,
    Paper,
    SimpleGrid,
    Stack,
    Tabs,
    Text,
    Title,
    Tooltip
} from "@mantine/core";
import {IconArrowLeft, IconCheck, IconCopy, IconFile, IconHomeFilled} from "@tabler/icons-react";
import {useQuery} from "@tanstack/react-query";
import {fetchPackageMarkdownOptions, fetchPackageOptions} from "#/logic/queries.ts";
import {useRegistryContext} from "#/context/RegistryContext.tsx";
import {BreadcrumItem} from "#/components/core/BreadcrumItem.tsx";
import {getLatestVersionNumber} from "#/logic/version.ts";
import {Description} from "#/components/python/package/Description.tsx";
import {VersionView} from "#/components/python/package/VersionView.tsx";
import {Overview} from "#/components/python/package/Overview.tsx";

export const Route = createFileRoute('/project/$pack')({
    component: RouteComponent,
})


function RouteComponent() {
    const {pack} = Route.useParams()
    const {config} = useRegistryContext()
    const {
        data,
        isError,
        error,
    } = useQuery(fetchPackageOptions(config?.url ?? "https://pypi.org", pack))

    const {
        data: markdown,
    } = useQuery(fetchPackageMarkdownOptions(config?.url ?? "https://pypi.org", pack))

    const breadcrumbItems = [
        {title: <IconHomeFilled size={18}/>, href: '/'},
        {title: "packages", href: '/project'},
        {title: pack, href: ''},
    ].map((item, index) => (
        <BreadcrumItem key={index} item={item}/>
    ));


    return (
        <Box pb={50}>
            {isError && <Box bg={"red"}>
                <Container pt={5} pb={5}>
                    <Stack gap={60} align={"center"}>
                        <Title order={3}>{error.message}</Title>
                    </Stack>
                </Container>
            </Box>}
            <div style={{backgroundColor: colourTheme.hero_body}}>
                <Container pt={40} pb={40}>
                    <Stack gap={60}>
                        <Stack>
                            <Flex justify={"space-between"}>
                                <Breadcrumbs>{breadcrumbItems}</Breadcrumbs>

                            </Flex>
                            <Flex>
                                <Button
                                    radius={3}
                                    leftSection={<IconArrowLeft size={16}/>}
                                    component={Link}
                                    to={"/"}
                                >
                                    Back to search
                                </Button>
                            </Flex>
                            <Flex justify={"space-between"} gap={30}>
                                <Stack gap={0}>
                                    <Title order={1} fw={500} fz={"36px"} c={"white"}
                                           ff={'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'}>
                                        {pack}
                                    </Title>
                                    <Text>{data?.summary}</Text>
                                    <Card withBorder mt={20} p={20} bg={"rgb(75 139 190 / 0.45)"}>
                                        Add command
                                        <Group pt={10} w={"100%"}>
                                            <Flex align={"center"} gap={10} w={350}>
                                                <Code p={10} fz={16} w={"95%"}>
                                                    <span
                                                        style={{color: "rgb(121, 192, 255)"}}>pip</span> install {pack}
                                                </Code>
                                                <CopyButton
                                                    value={`pip install ${pack}`}
                                                    timeout={2000}>
                                                    {({copied, copy}) => (
                                                        <Tooltip
                                                            label={copied ? 'Copied!' : 'Copy pull command'}
                                                            withArrow
                                                            position="left"
                                                        >
                                                            <ActionIcon
                                                                color={copied ? 'teal' : 'gray'}
                                                                variant="subtle"
                                                                onClick={copy}
                                                                size="sm"
                                                            >
                                                                {copied ? <IconCheck size={16}/> :
                                                                    <IconCopy size={16}/>}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Flex>
                                            <Divider orientation={"vertical"}/>
                                            <Flex align={"center"} gap={10} w={350}>
                                                <Code p={10} fz={16} w={"95%"}>
                                                    <span
                                                        style={{color: "rgb(121, 192, 255)"}}>uv</span> add {pack}
                                                </Code>
                                                <CopyButton
                                                    value={`uv add ${pack}`}
                                                    timeout={2000}>
                                                    {({copied, copy}) => (
                                                        <Tooltip
                                                            label={copied ? 'Copied!' : 'Copy pull command'}
                                                            withArrow
                                                            position="left"
                                                        >
                                                            <ActionIcon
                                                                color={copied ? 'teal' : 'gray'}
                                                                variant="subtle"
                                                                onClick={copy}
                                                                size="sm"
                                                            >
                                                                {copied ? <IconCheck size={16}/> :
                                                                    <IconCopy size={16}/>}
                                                            </ActionIcon>
                                                        </Tooltip>
                                                    )}
                                                </CopyButton>
                                            </Flex>
                                        </Group>
                                    </Card>
                                    {/*<HeaderCards data={data} />*/}

                                </Stack>
                                <DataList orientation="horizontal">
                                    <DataList.Item>
                                        <DataList.ItemLabel> Versions</DataList.ItemLabel>
                                        <DataList.ItemValue>{data?.versions.length ?? 0}</DataList.ItemValue>
                                    </DataList.Item>
                                    <DataList.Item>
                                        <DataList.ItemLabel> Latest</DataList.ItemLabel>
                                        <DataList.ItemValue>
                                            {getLatestVersionNumber(data?.versions.map((ver) => (ver.version ?? "0.0.0")) ?? [])}
                                        </DataList.ItemValue>
                                    </DataList.Item>
                                    {Object.keys(data?.project_urls ?? {}).map((urlKey, index) => (
                                        <DataList.Item key={index}>
                                            <DataList.ItemLabel>{urlKey}</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                <a href={data?.project_urls[urlKey]} target="_blank"
                                                   rel="noopener noreferrer">
                                                    {data?.project_urls[urlKey]}
                                                </a>
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                    ))}
                                    <DataList.Item>
                                        <DataList.ItemLabel>Licence</DataList.ItemLabel>
                                        <DataList.ItemValue>
                                            {data?.license ?? (data?.license_expression ?? "None")}
                                        </DataList.ItemValue>
                                    </DataList.Item>

                                </DataList>

                            </Flex>

                        </Stack>
                    </Stack>
                </Container>
            </div>
            <Container pt={40}>
                <Stack>
                    <Paper withBorder p={10}>
                        Add command
                        <SimpleGrid cols={2} pt={10} w={"100%"}>
                            <Flex align={"center"} gap={10}>
                                <Code p={10} fz={16} w={"95%"}>
                                    $ <span
                                    style={{color: "rgb(121, 192, 255)"}}>pip</span> install {pack}
                                </Code>
                                <CopyButton
                                    value={`pip install ${pack}`}
                                    timeout={2000}>
                                    {({copied, copy}) => (
                                        <Tooltip
                                            label={copied ? 'Copied!' : 'Copy pull command'}
                                            withArrow
                                            position="left"
                                        >
                                            <ActionIcon
                                                color={copied ? 'teal' : 'gray'}
                                                variant="subtle"
                                                onClick={copy}
                                                size="sm"
                                            >
                                                {copied ? <IconCheck size={16}/> : <IconCopy size={16}/>}
                                            </ActionIcon>
                                        </Tooltip>
                                    )}
                                </CopyButton>
                            </Flex>
                            <Flex align={"center"} gap={10}>
                                <Code p={10} fz={16} w={"95%"}>
                                    $ <span
                                    style={{color: "rgb(121, 192, 255)"}}>uv</span> add {pack}
                                </Code>
                                <CopyButton
                                    value={`uv add ${pack}`}
                                    timeout={2000}>
                                    {({copied, copy}) => (
                                        <Tooltip
                                            label={copied ? 'Copied!' : 'Copy pull command'}
                                            withArrow
                                            position="left"
                                        >
                                            <ActionIcon
                                                color={copied ? 'teal' : 'gray'}
                                                variant="subtle"
                                                onClick={copy}
                                                size="sm"
                                            >
                                                {copied ? <IconCheck size={16}/> : <IconCopy size={16}/>}
                                            </ActionIcon>
                                        </Tooltip>
                                    )}
                                </CopyButton>
                            </Flex>
                        </SimpleGrid>
                    </Paper>
                </Stack>
            </Container>

            <Container>
                <Tabs defaultValue="Overview" pt={20}>
                    <Tabs.List>
                        <Tabs.Tab value="Overview" leftSection={<IconFile size={12}/>}>
                            <Text fw={700} fz={"16px"}>
                                Overview
                            </Text>
                        </Tabs.Tab>
                        <Tabs.Tab value="README" leftSection={<IconFile size={12}/>}>
                            <Text fw={700} fz={"16px"}>
                                README
                            </Text>
                        </Tabs.Tab>
                        <Tabs.Tab value="versions">
                            <Text fw={700} fz={"16px"}>
                                Versions
                            </Text>
                        </Tabs.Tab>
                        {/*<Tabs.Tab value="Dependencies">
                            <Text fw={700} fz={"16px"}>
                                Dependencies
                            </Text>
                        </Tabs.Tab>*/}
                    </Tabs.List>

                    <Tabs.Panel value="Overview">
                        <Overview pack={data}/>
                    </Tabs.Panel>
                    <Tabs.Panel value="README">
                        <Description generated={markdown}/>
                    </Tabs.Panel>

                    <Tabs.Panel value="versions">
                        <VersionView data={data}/>
                    </Tabs.Panel>

                    {/*<Tabs.Panel value="versions">
                        <DependencyView data={data}/>
                    </Tabs.Panel>*/}

                </Tabs>
            </Container>
        </Box>
    )
}
