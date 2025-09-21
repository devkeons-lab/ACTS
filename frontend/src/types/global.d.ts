import { ReactElement, ReactNode } from 'react'

declare global {
  namespace JSX {
    interface Element extends ReactElement<any, any> { }
    interface ElementClass extends React.Component<any> {
      render(): ReactNode
    }
    interface ElementAttributesProperty { props: {} }
    interface ElementChildrenAttribute { children: {} }
    interface IntrinsicAttributes extends React.Attributes { }
    interface IntrinsicClassAttributes<T> extends React.ClassAttributes<T> { }
    interface IntrinsicElements {
      [elemName: string]: any
    }
  }
}

export {}