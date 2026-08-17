import {ActionIcon, Card, Code, CopyButton, Flex, Stack, Text, Title, Tooltip} from "@mantine/core";
import {IconCheck, IconCopy, IconSearch} from "@tabler/icons-react";
import type {PackageInfo} from "#/logic/types.ts";

interface Props {
    data?: PackageInfo
}

export function ProvidesExtraCard({data}: Props) {
    return (
        <Card pt={20} p={10} withBorder shadow={"md"}>
            <Flex gap={10}>
                <IconSearch/>
                <Title order={4} pb={10}>Variants</Title>
            </Flex>
            <Stack gap={0}>
                {((data?.provides_extra.length ?? 0) > 0) && data?.provides_extra.map((value) =>
                    (
                        <Flex align={"center"}>
                            <Code p={10} fz={16} w={"95%"}>
                                <span style={{color: "rgb(121, 192, 255)"}}>pip</span> install '{data?.name}[{value}]'
                            </Code>
                            <CopyButton
                                value={`pip install '${data?.name}[${value}]'`}
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

                    )
                )}
            </Stack>
            <Text>{((data?.provides_extra.length ?? 0) <= 0) && "None"}</Text>
        </Card>
    );
}